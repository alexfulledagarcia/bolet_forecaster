import unittest
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.geography_service import GeographyService
from app.services.weather_service import WeatherService
from app.models.prediction_model import PredictionModel
from app.models.species import Species


class TestBoletForecaster(unittest.TestCase):

    def setUp(self):
        self.geo = GeographyService()
        self.weather_svc = WeatherService()

    def test_species_catalog(self):
        species = self.geo.get_all_species()
        self.assertGreaterEqual(len(species), 8)
        ids = [s.id for s in species]
        self.assertIn("cep", ids)
        self.assertIn("rovello", ids)
        self.assertIn("camagroc", ids)
        self.assertIn("trompeta", ids)
        self.assertIn("ou_de_reig", ids)

    def test_geography_zones(self):
        zones = self.geo.get_all_zones()
        self.assertGreaterEqual(len(zones), 50)
        comarques = self.geo.get_comarques()
        self.assertIn("Berguedà", comarques)
        self.assertIn("Ripollès", comarques)
        self.assertIn("Osona", comarques)

    def test_nearest_zone_finder(self):
        # Coordinates near Berga / Rasos de Peguera (42.14, 1.76)
        nearest = self.geo.find_nearest_zone(42.14, 1.76)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest["comarca"], "Berguedà")

    def test_prediction_model_ideal_conditions(self):
        cep = self.geo.get_species_by_id("cep")
        zone = self.geo.get_zone_by_id("bergueda_rasos")

        # Ideal weather for Cep
        ideal_weather = {
            "rain_14d_mm": 85.0,
            "rain_7d_mm": 30.0,
            "soil_moisture_pct": 36.0,
            "temp_mean_c": 14.5,
            "temp_min_c": 8.0,
            "temp_max_c": 19.0,
            "history": []
        }

        forecast = PredictionModel.calculate_forecast(zone, ideal_weather, cep)
        self.assertGreaterEqual(forecast.probability, 70.0)
        self.assertIn("Excel·lent", forecast.rating_label)
        self.assertIsNotNone(forecast.explanation)
        self.assertIn("85.0 mm", forecast.explanation.rain_detail)
        self.assertIn("Obaga", forecast.explanation.aspect_detail)

    def test_prediction_model_drought_conditions(self):
        cep = self.geo.get_species_by_id("cep")
        zone = self.geo.get_zone_by_id("bergueda_rasos")

        # Severe drought
        drought_weather = {
            "rain_14d_mm": 2.0,
            "rain_7d_mm": 0.0,
            "soil_moisture_pct": 10.0,
            "temp_mean_c": 26.0,
            "temp_min_c": 15.0,
            "temp_max_c": 32.0,
            "history": []
        }

        forecast = PredictionModel.calculate_forecast(zone, drought_weather, cep)
        self.assertLessEqual(forecast.probability, 25.0)
        self.assertIn("Dèficit hídric", forecast.explanation.rain_detail)

    def test_prediction_model_habitat_mismatch(self):
        ou_de_reig = self.geo.get_species_by_id("ou_de_reig")
        # Rasos de Peguera is subalpine Pinus uncinata at 1780m, not thermophilic oak/chestnut
        zone = self.geo.get_zone_by_id("bergueda_rasos")

        weather = {
            "rain_14d_mm": 60.0,
            "rain_7d_mm": 20.0,
            "soil_moisture_pct": 30.0,
            "temp_mean_c": 18.0,
            "temp_min_c": 12.0,
            "temp_max_c": 24.0,
            "history": []
        }

        forecast = PredictionModel.calculate_forecast(zone, weather, ou_de_reig)
        # Because altitude (1780m) is way above max (950m) and forest is pine negre, probability must be low
        self.assertLess(forecast.probability, 35.0)

    def test_frost_penalty_on_sensitive_species(self):
        cep = self.geo.get_species_by_id("cep")
        fredolic = self.geo.get_species_by_id("fredolic")
        zone = self.geo.get_zone_by_id("bergueda_rasos")

        frost_weather = {
            "rain_14d_mm": 60.0,
            "rain_7d_mm": 20.0,
            "soil_moisture_pct": 30.0,
            "temp_mean_c": 4.0,
            "temp_min_c": -3.0,
            "temp_max_c": 9.0,
            "history": []
        }

        forecast_cep = PredictionModel.calculate_forecast(zone, frost_weather, cep)
        forecast_fredolic = PredictionModel.calculate_forecast(zone, frost_weather, fredolic)

        # Fredolic should handle cold and frost much better than Cep
        self.assertGreater(forecast_fredolic.probability, forecast_cep.probability)


if __name__ == "__main__":
    unittest.main()

