from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Species(BaseModel):
    id: str
    name_ca: str
    name_es: str
    scientific_name: str
    icon: str
    color: str
    description: str
    season: str
    habitats: List[str]
    preferred_aspect: List[str]
    elevation_min_m: float
    elevation_max_m: float
    optimal_elevation_m: List[float]
    optimal_temp_mean_c: List[float]
    temp_min_c: float
    temp_max_c: float
    rain_trigger_14d_min_mm: float
    rain_trigger_14d_optimal_mm: List[float]
    recent_rain_7d_optimal_mm: List[float]
    min_soil_moisture: float
    optimal_soil_moisture: List[float]
    frost_sensitivity: str
    toxicity_warning: str


class FactorBreakdown(BaseModel):
    rain_score: float = Field(..., description="0-100 score based on 14d and 7d precipitation")
    rain_14d_mm: float
    rain_7d_mm: float
    soil_score: float = Field(..., description="0-100 score based on soil moisture")
    soil_moisture_pct: float
    temp_score: float = Field(..., description="0-100 score based on temperature regime")
    temp_mean_c: float
    temp_min_c: float
    temp_max_c: float
    habitat_score: float = Field(..., description="0-100 score based on forest tree compatibility")
    elevation_score: float = Field(..., description="0-100 score based on altitude match")
    aspect_score: float = Field(..., description="0-100 score based on shading/aspect (Obaga vs Solana)")


class ZoneExplanation(BaseModel):
    rating_ca: str
    rating_en: str
    badge_color: str
    summary_ca: str
    summary_en: str
    rain_detail: str
    soil_detail: str
    temp_detail: str
    habitat_detail: str
    aspect_detail: str
    forager_tips: str
    toxicity_warning: str


class WeatherHistoryPoint(BaseModel):
    date: str
    precipitation_mm: float
    temp_max_c: float
    temp_min_c: float
    soil_moisture: float


class ZoneForecast(BaseModel):
    zone_id: str
    name: str
    comarca: str
    region: str
    lat: float
    lon: float
    elevation_m: int
    aspect: str
    forest_type: str
    soil_type: str
    notes: Optional[str] = None
    probability: float
    rating_label: str
    factors: FactorBreakdown
    explanation: Optional[ZoneExplanation] = None
    history: Optional[List[WeatherHistoryPoint]] = None

