// Leaflet Map and Heatmap Handler
let map = null;
let heatLayer = null;
let markersLayer = null;
let activeMarkerCircle = null;
let onZoneSelect = null;
let currentBaseLayer = "dark";

// Tile Providers
const TILE_LAYERS = {
  dark: L.layerGroup([
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: '&copy; Esri, DeLorme, &copy; OpenStreetMap',
      maxZoom: 16
    }),
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      attribution: '',
      maxZoom: 16
    })
  ]),
  osm: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
    maxZoom: 18
  }),
  satellite: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: '&copy; Esri',
    maxZoom: 18
  })
};

function initMap(zoneSelectCallback) {
  onZoneSelect = zoneSelectCallback;

  // Center on Catalonia
  map = L.map("map", {
    center: [41.78, 1.85],
    zoom: 8,
    minZoom: 7,
    maxZoom: 15,
    layers: [TILE_LAYERS.dark],
    zoomControl: true
  });

  // Layer groups
  markersLayer = L.layerGroup().addTo(map);

  // Map click handler: selects nearest zone if clicked on open map
  map.on("click", function(e) {
    if (onZoneSelect) {
      onZoneSelect(null, e.latlng.lat, e.latlng.lng);
    }
  });

  return map;
}

function setBaseLayer(layerKey) {
  if (!TILE_LAYERS[layerKey] || currentBaseLayer === layerKey) return;

  map.removeLayer(TILE_LAYERS[currentBaseLayer]);
  map.addLayer(TILE_LAYERS[layerKey]);
  // Ensure layers are underneath markers & heatmap
  if (typeof TILE_LAYERS[layerKey].bringToBack === "function") {
    TILE_LAYERS[layerKey].bringToBack();
  } else if (TILE_LAYERS[layerKey].eachLayer) {
    TILE_LAYERS[layerKey].eachLayer(l => {
      if (typeof l.bringToBack === "function") l.bringToBack();
    });
  }
  currentBaseLayer = layerKey;
}

function updateMapData(zones, heatmapPoints) {
  // 1. Update or create Heatmap Layer
  if (heatLayer) {
    map.removeLayer(heatLayer);
  }

  if (heatmapPoints && heatmapPoints.length > 0 && typeof L.heatLayer === "function") {
    heatLayer = L.heatLayer(heatmapPoints, {
      radius: 38,
      blur: 26,
      maxZoom: 12,
      max: 1.0,
      gradient: {
        0.20: "#ef4444", // Minimum Red (<=50%)
        0.50: "#ef4444", // Red at 50%
        0.62: "#f97316", // Orange
        0.75: "#eab308", // Yellow at 75%
        0.86: "#84cc16", // Lime Green
        1.00: "#10b981"  // Vibrant Green (Optimal)
      }
    }).addTo(map);
  }

  // 2. Update Interactive Markers - completely stationary
  markersLayer.clearLayers();

  zones.forEach(zone => {
    const prob = zone.probability;
    const color = getProbColor(prob);
    const radius = Math.max(6, Math.min(13, Math.round(prob / 8)));

    const circle = L.circleMarker([zone.lat, zone.lon], {
      radius: radius,
      fillColor: color,
      color: prob >= 75 ? "#f8fafc" : "#e2e8f0",
      weight: prob >= 75 ? 2.5 : 1.5,
      opacity: 0.95,
      fillOpacity: 0.85
    });

    // Tooltip
    circle.bindTooltip(`
      <div style="font-family: var(--font-family); padding: 4px;">
        <strong style="color: #f8fafc; font-size: 12px;">${zone.name}</strong><br/>
        <span style="color: #94a3b8; font-size: 11px;">${zone.comarca} (${zone.elevation_m}m)</span><br/>
        <span style="color: ${color}; font-weight: bold; font-size: 12px;">${zone.probability}% - ${zone.rating_label}</span>
      </div>
    `, { direction: "top", offset: [0, -6], className: "custom-leaflet-tooltip" });

    circle.on("click", function(e) {
      L.DomEvent.stopPropagation(e);
      highlightMarker(zone.lat, zone.lon);
      if (onZoneSelect) {
        onZoneSelect(zone.zone_id);
      }
    });

    circle.zoneId = zone.zone_id;
    markersLayer.addLayer(circle);
  });
}

function highlightMarker(lat, lon) {
  if (activeMarkerCircle) {
    map.removeLayer(activeMarkerCircle);
  }

  activeMarkerCircle = L.circleMarker([lat, lon], {
    radius: 18,
    fillColor: "transparent",
    color: "#38bdf8",
    weight: 3,
    dashArray: "4, 4",
    opacity: 1.0
  }).addTo(map);
}

function flyToCoordinates(lat, lon, zoom = 10) {
  if (map) {
    map.flyTo([lat, lon], zoom, { duration: 1.0 });
    highlightMarker(lat, lon);
  }
}

function toggleHeatmap(visible) {
  if (!heatLayer) return;
  if (visible) {
    if (!map.hasLayer(heatLayer)) map.addLayer(heatLayer);
  } else {
    if (map.hasLayer(heatLayer)) map.removeLayer(heatLayer);
  }
}

function toggleMarkers(visible) {
  if (!markersLayer) return;
  if (visible) {
    if (!map.hasLayer(markersLayer)) map.addLayer(markersLayer);
  } else {
    if (map.hasLayer(markersLayer)) map.removeLayer(markersLayer);
  }
}

function getProbColor(prob) {
  if (prob >= 85) return "#10b981"; // Vibrant Green (Optimal >85%)
  if (prob >= 78) return "#84cc16"; // Lime Green (Good)
  if (prob >= 68) return "#eab308"; // Yellow (at ~75%)
  if (prob >= 55) return "#f97316"; // Orange
  return "#ef4444";                 // Red (50% and below is the minimum color)
}
