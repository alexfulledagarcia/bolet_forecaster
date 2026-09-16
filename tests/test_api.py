import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from app.main import app


class TestBoletForecasterAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bolet Forecaster Catalunya", response.text)

    def test_get_species(self):
        response = self.client.get("/api/species")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 8)
        names = [s["id"] for s in data]
        self.assertIn("cep", names)
        self.assertIn("rovello", names)
        self.assertIn("camagroc", names)

    def test_get_comarques(self):
        response = self.client.get("/api/comarques")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Berguedà", data)
        self.assertIn("Ripollès", data)

    def test_get_forecast(self):
        response = self.client.get("/api/forecast?species_id=cep")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("species", data)
        self.assertIn("zones", data)
        self.assertIn("heatmap_points", data)
        self.assertGreaterEqual(data["total_zones"], 50)
        self.assertEqual(len(data["zones"]), data["total_zones"])
        self.assertEqual(len(data["heatmap_points"]), data["total_zones"])

        # Check zone structure
        first_zone = data["zones"][0]
        self.assertIn("zone_id", first_zone)
        self.assertIn("probability", first_zone)
        self.assertIn("rating_label", first_zone)
        self.assertIn("factors", first_zone)

        # Check heatmap point structure: [lat, lon, intensity]
        first_hm = data["heatmap_points"][0]
        self.assertEqual(len(first_hm), 3)
        self.assertGreaterEqual(first_hm[2], 0.0)
        self.assertLessEqual(first_hm[2], 1.0)

    def test_get_zone_detail(self):
        response = self.client.get("/api/zone/bergueda_rasos?species_id=cep")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["zone_id"], "bergueda_rasos")
        self.assertIn("factors", data)
        self.assertIn("explanation", data)
        self.assertIn("summary_ca", data["explanation"])
        self.assertIn("rain_detail", data["explanation"])
        self.assertIn("history", data)
        self.assertGreaterEqual(len(data["history"]), 14)

    def test_get_nearest_zone(self):
        response = self.client.get("/api/nearest-zone?lat=42.14&lon=1.76&species_id=cep")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["zone_id"], "bergueda_rasos")

    def test_nonexistent_species_404(self):
        response = self.client.get("/api/forecast?species_id=invalid_species_xyz")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

