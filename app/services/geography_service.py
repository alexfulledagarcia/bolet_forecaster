import os
import json
import math
from typing import List, Dict, Any, Optional
from app.models.species import Species

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
GRID_FILE = os.path.join(DATA_DIR, "catalonia_grid.json")
SPECIES_FILE = os.path.join(DATA_DIR, "species_catalog.json")


class GeographyService:
    def __init__(self, grid_file: str = GRID_FILE, species_file: str = SPECIES_FILE):
        self.grid_file = grid_file
        self.species_file = species_file
        self._zones: List[Dict[str, Any]] = self._load_zones()
        self._species_catalog: Dict[str, Species] = self._load_species()

    def _load_zones(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.grid_file):
            raise FileNotFoundError(f"Grid file not found: {self.grid_file}")
        with open(self.grid_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_species(self) -> Dict[str, Species]:
        if not os.path.exists(self.species_file):
            raise FileNotFoundError(f"Species catalog not found: {self.species_file}")
        with open(self.species_file, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            catalog = {}
            for item in raw_list:
                sp = Species(**item)
                catalog[sp.id] = sp
            return catalog

    def get_all_zones(self) -> List[Dict[str, Any]]:
        return self._zones

    def get_zone_by_id(self, zone_id: str) -> Optional[Dict[str, Any]]:
        for z in self._zones:
            if z["id"] == zone_id:
                return z
        return None

    def get_all_species(self) -> List[Species]:
        return list(self._species_catalog.values())

    def get_species_by_id(self, species_id: str) -> Optional[Species]:
        return self._species_catalog.get(species_id)

    def get_comarques(self) -> List[str]:
        return sorted(list(set(z["comarca"] for z in self._zones)))

    def find_nearest_zone(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not self._zones:
            return None

        best_zone = None
        min_dist_sq = float("inf")

        for z in self._zones:
            d_lat = z["lat"] - lat
            # Adjust longitude by cos(lat)
            d_lon = (z["lon"] - lon) * math.cos(math.radians(lat))
            dist_sq = d_lat * d_lat + d_lon * d_lon
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_zone = z

        return best_zone

