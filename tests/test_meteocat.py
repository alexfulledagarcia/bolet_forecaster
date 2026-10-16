import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.meteocat_service import MeteocatService, MeteocatAPIError
from app.services.weather_service import WeatherService


class TestMeteocatIntegration(unittest.TestCase):

    def test_meteocat_not_configured_by_default(self):
        service = MeteocatService(api_key="")
        self.assertFalse(service.is_configured)
        with self.assertRaises(MeteocatAPIError):
            service.fetch_weather_for_zones([{"id": "test", "lat": 42.0, "lon": 2.0}])

    def test_haversine_distance_calculation(self):
        # Distance between Barcelona (41.3879, 2.16992) and Girona (41.9794, 2.8214) ~ 85-90 km
        dist = MeteocatService._haversine_distance_km(41.3879, 2.16992, 41.9794, 2.8214)
        self.assertGreater(dist, 80)
        self.assertLess(dist, 100)

    def test_find_nearest_station(self):
        service = MeteocatService(api_key="dummy")
        stations = [
            {"codi": "BCN", "coordenades": {"latitud": 41.38, "longitud": 2.17}},
            {"codi": "PIR", "coordenades": {"latitud": 42.45, "longitud": 1.95}}
        ]
        nearest = service.find_nearest_station(42.40, 1.90, stations)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest["codi"], "PIR")

    @patch.object(MeteocatService, "fetch_weather_for_zones")
    def test_weather_service_fallback_on_meteocat_failure(self, mock_meteocat_fetch):
        # Simulate Meteocat throwing an error (e.g. rate limit, quota, timeout)
        mock_meteocat_fetch.side_effect = MeteocatAPIError("Rate limit reached", status_code=429)

        ws = WeatherService(cache_file="data/cache/test_weather_cache.json")
        ws.meteocat.api_key = "test_key"  # Set key so it attempts Meteocat

        # Mock Open-Meteo to return successful data
        with patch.object(ws, "_fetch_from_open_meteo") as mock_om:
            mock_om.return_value = {
                "test_zone": {
                    "zone_id": "test_zone",
                    "rain_14d_mm": 45.0,
                    "rain_7d_mm": 20.0,
                    "soil_moisture_pct": 30.0,
                    "temp_mean_c": 16.0,
                    "temp_min_c": 9.0,
                    "temp_max_c": 22.0,
                    "history": []
                }
            }

            zones = [{"id": "test_zone", "lat": 42.14, "lon": 1.765}]
            result = ws.get_weather_for_zones(zones, force_refresh=True)

            # Verification: Meteocat was called, failed, and Open-Meteo was called as fallback
            mock_meteocat_fetch.assert_called_once()
            mock_om.assert_called_once()
            self.assertIn("test_zone", result)
            self.assertEqual(result["test_zone"]["rain_14d_mm"], 45.0)

        # Cleanup test cache if created
        if os.path.exists("data/cache/test_weather_cache.json"):
            os.remove("data/cache/test_weather_cache.json")

    def test_force_update_skips_cache(self):
        import time
        ws = WeatherService(cache_file="data/cache/test_force_cache.json")
        ws.meteocat.api_key = "test_meteocat_key"

        # Populate cache with existing data
        ws._cache = {
            "timestamp": time.time(),  # Very fresh cache
            "zones": {
                "zone_1": {
                    "zone_id": "zone_1",
                    "rain_14d_mm": 10.0,
                    "rain_7d_mm": 5.0,
                    "soil_moisture_pct": 20.0,
                    "temp_mean_c": 15.0,
                    "temp_min_c": 10.0,
                    "temp_max_c": 20.0,
                    "history": []
                }
            }
        }

        with patch.object(ws.meteocat, "fetch_weather_for_zones") as mock_meteocat:
            mock_meteocat.return_value = {
                "zone_1": {
                    "zone_id": "zone_1",
                    "rain_14d_mm": 99.0,  # Updated rain
                    "rain_7d_mm": 50.0,
                    "soil_moisture_pct": 45.0,
                    "temp_mean_c": 14.0,
                    "temp_min_c": 8.0,
                    "temp_max_c": 19.0,
                    "history": []
                }
            }

            zones = [{"id": "zone_1", "lat": 42.0, "lon": 2.0}]

            # 1. Without force_update: should use fresh cache without calling Meteocat
            res_cached = ws.get_weather_for_zones(zones, force_update=False)
            mock_meteocat.assert_not_called()
            self.assertEqual(res_cached["zone_1"]["rain_14d_mm"], 10.0)

            # 2. With force_update=True: should bypass cache and call Meteocat
            res_fresh = ws.get_weather_for_zones(zones, force_update=True)
            mock_meteocat.assert_called_once()
            self.assertEqual(res_fresh["zone_1"]["rain_14d_mm"], 99.0)

        if os.path.exists("data/cache/test_force_cache.json"):
            os.remove("data/cache/test_force_cache.json")


if __name__ == "__main__":
    unittest.main()

