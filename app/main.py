import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.services.geography_service import GeographyService
from app.services.weather_service import WeatherService
from app.models.prediction_model import PredictionModel
from app.models.species import Species, ZoneForecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bolet_forecaster")

app = FastAPI(
    title="Bolet Forecaster Catalunya",
    description="Previsió i mapa de probabilitat de bolets comestibles a Catalunya basat en dades meteorològiques obertes i models ecològics.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services initialization
geo_service = GeographyService()
weather_service = WeatherService()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")


@app.get("/api/species", response_model=List[Species])
def get_species():
    """Returns all supported edible mushroom species."""
    return geo_service.get_all_species()


@app.get("/api/comarques", response_model=List[str])
def get_comarques():
    """Returns list of comarques represented in Catalonia."""
    return geo_service.get_comarques()


@app.get("/api/forecast")
def get_forecast(
    species_id: str = Query("cep", description="Identifier of the mushroom species"),
    comarca: Optional[str] = Query(None, description="Optional comarca filter"),
    force_refresh: bool = Query(False, description="Force refresh of weather cache")
):
    """
    Returns probability forecasts for all zones across Catalonia for the chosen species.
    Used to render the Leaflet map and heatmap layer.
    """
    species = geo_service.get_species_by_id(species_id)
    if not species:
        raise HTTPException(status_code=404, detail=f"Species '{species_id}' not found.")

    zones = geo_service.get_all_zones()
    if comarca:
        zones = [z for z in zones if z["comarca"].lower() == comarca.lower()]

    weather_data = weather_service.get_weather_for_zones(zones, force_refresh=force_refresh)

    forecasts: List[Dict[str, Any]] = []
    # Heatmap points array format: [lat, lon, intensity (0.0 to 1.0)]
    heatmap_points: List[List[float]] = []

    for z in zones:
        w = weather_data.get(z["id"], {})
        zf = PredictionModel.calculate_forecast(z, w, species)
        forecasts.append(zf.model_dump())
        intensity = round(zf.probability / 100.0, 3)
        heatmap_points.append([z["lat"], z["lon"], intensity])

    # Sort by probability descending
    forecasts.sort(key=lambda x: x["probability"], reverse=True)

    return {
        "species": species.model_dump(),
        "total_zones": len(forecasts),
        "zones": forecasts,
        "heatmap_points": heatmap_points
    }


@app.get("/api/zone/{zone_id}", response_model=ZoneForecast)
def get_zone_forecast(
    zone_id: str,
    species_id: str = Query("cep", description="Identifier of the mushroom species")
):
    """
    Returns in-depth prediction, complete natural language explanation,
    and 17-day weather trend history for a specific zone.
    """
    zone = geo_service.get_zone_by_id(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    species = geo_service.get_species_by_id(species_id)
    if not species:
        raise HTTPException(status_code=404, detail=f"Species '{species_id}' not found.")

    weather_dict = weather_service.get_weather_for_zones([zone])
    w = weather_dict.get(zone["id"], {})

    return PredictionModel.calculate_forecast(zone, w, species)


@app.get("/api/nearest-zone")
def get_nearest_zone(
    lat: float = Query(..., description="Latitude of clicked point"),
    lon: float = Query(..., description="Longitude of clicked point"),
    species_id: str = Query("cep", description="Species id")
):
    """
    Finds the nearest zone to any arbitrary coordinate clicked on the map
    and returns its detailed forecast and explanation.
    """
    nearest = geo_service.find_nearest_zone(lat, lon)
    if not nearest:
        raise HTTPException(status_code=404, detail="No zone found.")

    species = geo_service.get_species_by_id(species_id)
    if not species:
        raise HTTPException(status_code=404, detail=f"Species '{species_id}' not found.")

    weather_dict = weather_service.get_weather_for_zones([nearest])
    w = weather_dict.get(nearest["id"], {})

    forecast = PredictionModel.calculate_forecast(nearest, w, species)
    return forecast.model_dump()


@app.post("/api/weather/refresh")
def refresh_weather():
    """Forces refreshing of Open-Meteo weather data for all zones."""
    zones = geo_service.get_all_zones()
    weather_dict = weather_service.get_weather_for_zones(zones, force_refresh=True)
    return {"status": "success", "refreshed_zones": len(weather_dict)}


@app.get("/api/summary")
def get_summary():
    """Returns general statistics and metadata."""
    species_list = geo_service.get_all_species()
    zones = geo_service.get_all_zones()
    comarques = geo_service.get_comarques()
    return {
        "species_count": len(species_list),
        "zone_count": len(zones),
        "comarques_count": len(comarques),
        "comarques": comarques
    }


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
@app.head("/")
def read_root():
    """Serves the main application page."""
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return {"message": "Bolet Forecaster API is running. Web UI not found."}
