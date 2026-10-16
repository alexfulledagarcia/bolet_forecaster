import os
import json
import time
import math
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cache")
STATIONS_CACHE_FILE = os.path.join(CACHE_DIR, "meteocat_stations.json")


class MeteocatAPIError(Exception):
    """Exception raised when an error occurs while communicating with Meteocat API."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class MeteocatService:
    """
    Client for Servei Meteorològic de Catalunya (Meteocat) REST API.
    Docs: https://apidocs.meteocat.gencat.cat/
    
    Authenticates via the 'X-Api-Key' HTTP header.
    Supports querying station metadata (XEMA) and observations/forecasts,
    mapping Catalonia zones to the nearest meteorological stations.
    """

    BASE_URL = "https://api.meteo.cat"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = (api_key or os.environ.get("METEOCAT_API_KEY", "")).strip()
        self.timeout = timeout
        self._stations_cache: Optional[List[Dict[str, Any]]] = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a Meteocat API key is provided."""
        return bool(self.api_key)

    def _make_request(self, endpoint: str) -> Any:
        """
        Executes an authorized GET request to Meteocat API.
        Raises MeteocatAPIError on non-200 responses, rate limits, or timeouts.
        """
        if not self.is_configured:
            raise MeteocatAPIError("Meteocat API key is not configured.", status_code=401)

        url = f"{self.BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
            "User-Agent": "BoletForecaster/1.0"
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            msg = f"Meteocat API HTTP {e.code} for {endpoint}: {e.reason}. {body}".strip()
            logger.warning(msg)
            raise MeteocatAPIError(msg, status_code=e.code)
        except urllib.error.URLError as e:
            msg = f"Meteocat network connection error for {endpoint}: {e.reason}"
            logger.warning(msg)
            raise MeteocatAPIError(msg)
        except Exception as e:
            msg = f"Unexpected error querying Meteocat {endpoint}: {e}"
            logger.warning(msg)
            raise MeteocatAPIError(msg)

    def get_stations(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetches and caches metadata for operational XEMA stations across Catalonia.
        Endpoint: /xema/v1/estacions/metadades?estat=ope
        """
        if not force_refresh and self._stations_cache:
            return self._stations_cache

        # Check local disk cache
        if not force_refresh and os.path.exists(STATIONS_CACHE_FILE):
            try:
                with open(STATIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                    self._stations_cache = json.load(f)
                    if self._stations_cache:
                        return self._stations_cache
            except Exception as e:
                logger.warning(f"Failed to read Meteocat stations cache: {e}")

        # Fetch from API
        data = self._make_request("/xema/v1/estacions/metadades?estat=ope")
        if isinstance(data, list):
            self._stations_cache = data
            try:
                os.makedirs(os.path.dirname(STATIONS_CACHE_FILE), exist_ok=True)
                with open(STATIONS_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"Could not write Meteocat stations cache: {e}")
            return self._stations_cache
        return []

    @staticmethod
    def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates geographic distance in km between two coordinate points."""
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    def find_nearest_station(self, lat: float, lon: float, stations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Finds the closest XEMA station for given coordinates."""
        closest_station = None
        min_dist = float("inf")

        for st in stations:
            # Handle various potential coordinate key formats
            st_lat = None
            st_lon = None
            if "coordenades" in st and isinstance(st["coordenades"], dict):
                st_lat = st["coordenades"].get("latitud")
                st_lon = st["coordenades"].get("longitud")
            elif "latitud" in st and "longitud" in st:
                st_lat = st.get("latitud")
                st_lon = st.get("longitud")

            if st_lat is not None and st_lon is not None:
                dist = self._haversine_distance_km(lat, lon, float(st_lat), float(st_lon))
                if dist < min_dist:
                    min_dist = dist
                    closest_station = st

        return closest_station

    def fetch_weather_for_zones(self, zones: List[Dict[str, Any]], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Fetches real-time / recent meteorological indicators from Meteocat for each zone.
        Maps zones to nearby stations or municipal forecasts.
        If force_refresh is True, cached station metadata is bypassed.
        If an error or quota limit is encountered, raises MeteocatAPIError to trigger fallback.
        """
        if not self.is_configured:
            raise MeteocatAPIError("METEOCAT_API_KEY is not set.")

        stations = self.get_stations(force_refresh=force_refresh)
        if not stations:
            raise MeteocatAPIError("No operational Meteocat stations returned.")

        results: Dict[str, Dict[str, Any]] = {}
        now = time.time()
        import datetime
        today = datetime.date.today()

        # Query Meteocat data for the requested zones
        for z in zones:
            z_id = z["id"]
            z_lat = z["lat"]
            z_lon = z["lon"]
            st = self.find_nearest_station(z_lat, z_lon, stations)
            st_code = st.get("codi") if st else None

            if not st_code:
                continue

            # Fetch daily statistics for Variable 32 (Temperature) and 36 (Precipitation)
            # or municipal forecast endpoint.
            # Example endpoint: /xema/v1/variables/estadistics/diaris/36?codiEstacio={st_code}&any={today.year}&mes={today.month}
            try:
                precip_data = self._make_request(
                    f"/xema/v1/variables/estadistics/diaris/36?codiEstacio={st_code}&any={today.year}&mes={today.month}"
                )
                temp_data = self._make_request(
                    f"/xema/v1/variables/estadistics/diaris/32?codiEstacio={st_code}&any={today.year}&mes={today.month}"
                )
                
                # Parse daily values
                processed = self._process_station_data(z, precip_data, temp_data, today)
                processed["source"] = "meteocat"
                results[z_id] = processed
            except MeteocatAPIError:
                raise
            except Exception as e:
                logger.warning(f"Failed processing Meteocat data for zone {z_id} (station {st_code}): {e}")
                continue

        if not results:
            raise MeteocatAPIError("Meteocat did not return valid weather data for any zones.")

        return results

    def _process_station_data(
        self,
        zone_obj: Dict[str, Any],
        precip_data: Any,
        temp_data: Any,
        today: Any
    ) -> Dict[str, Any]:
        """Converts Meteocat measurements into the standardized weather dict format."""
        import datetime
        
        # Accumulate precipitation from daily values
        daily_precip: Dict[str, float] = {}
        if isinstance(precip_data, list):
            for item in precip_data:
                # Format: {"data": "2024-10-15T00:00Z", "valor": 12.4, ...}
                d_str = item.get("data", "")[:10]
                val = float(item.get("valor", 0.0) or 0.0)
                if d_str:
                    daily_precip[d_str] = val

        # Daily temperatures
        daily_temp_max: Dict[str, float] = {}
        daily_temp_min: Dict[str, float] = {}
        daily_temp_mean: Dict[str, float] = {}
        if isinstance(temp_data, list):
            for item in temp_data:
                d_str = item.get("data", "")[:10]
                val = item.get("valor")
                val_float = float(val) if val is not None else 15.0
                if d_str:
                    daily_temp_mean[d_str] = val_float
                    daily_temp_max[d_str] = float(item.get("maxim", val_float + 4.0) or (val_float + 4.0))
                    daily_temp_min[d_str] = float(item.get("minim", val_float - 4.0) or (val_float - 4.0))

        # Build 17-day history (14 days past + today + 2 forecast days)
        history = []
        rain_14d = 0.0
        rain_7d = 0.0
        temps_last_7 = []

        for offset in range(-14, 3):
            cur_date = today + datetime.timedelta(days=offset)
            date_str = cur_date.strftime("%Y-%m-%d")
            p = daily_precip.get(date_str, 0.0)
            t_max = daily_temp_max.get(date_str, 18.0)
            t_min = daily_temp_min.get(date_str, 9.0)
            t_mean = daily_temp_mean.get(date_str, (t_max + t_min) / 2.0)

            if -14 <= offset < 0:
                rain_14d += p
                if offset >= -7:
                    rain_7d += p
                    temps_last_7.append(t_mean)

            history.append({
                "date": date_str,
                "precipitation_mm": round(p, 1),
                "temp_max_c": round(t_max, 1),
                "temp_min_c": round(t_min, 1),
                "soil_moisture": round(min(0.5, max(0.1, 0.15 + (rain_7d / 100.0) * 0.3)), 3)
            })

        avg_temp = round(sum(temps_last_7) / len(temps_last_7), 1) if temps_last_7 else 14.5
        all_t_mins = [h["temp_min_c"] for h in history[:14]]
        all_t_maxs = [h["temp_max_c"] for h in history[:14]]

        return {
            "zone_id": zone_obj["id"],
            "rain_14d_mm": round(rain_14d, 1),
            "rain_7d_mm": round(rain_7d, 1),
            "soil_moisture_pct": round(min(55.0, max(15.0, 18.0 + rain_7d * 0.45)), 1),
            "temp_mean_c": avg_temp,
            "temp_min_c": round(min(all_t_mins), 1) if all_t_mins else 8.0,
            "temp_max_c": round(max(all_t_maxs), 1) if all_t_maxs else 21.0,
            "history": history
        }

