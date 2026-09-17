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
      radius: 28,
      blur: 18,
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
    const radius = Math.max(5, Math.min(10, Math.round(prob / 10)));

    const circle = L.circleMarker([zone.lat, zone.lon], {
      radius: radius,
      fillColor: color,
      color: prob >= 75 ? "#f8fafc" : "#cbd5e1",
      weight: prob >= 75 ? 2 : 1.2,
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

function clearHighlightMarker() {
  if (activeMarkerCircle && map) {
    map.removeLayer(activeMarkerCircle);
    activeMarkerCircle = null;
  }
}

function resetMapView() {
  if (map) {
    map.flyTo([41.78, 1.85], 8, { duration: 0.8 });
  }
  clearHighlightMarker();
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

// ---------------------------------------------------------------------------
// Fine-Grain Zone Detailed Sub-Map Handler
// ---------------------------------------------------------------------------
let subMap = null;
let subMapLayers = {};
let subMapCurrentLayer = "satellite";
let subMapItemsLayer = null;
let currentDetailZone = null;

function initDetailSubMap() {
  if (subMap) return;

  subMapLayers = {
    satellite: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      attribution: '&copy; Esri',
      maxZoom: 18
    }),
    topo: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
      attribution: '&copy; Esri Topo',
      maxZoom: 18
    })
  };

  subMap = L.map("detailSubMap", {
    center: [41.78, 1.85],
    zoom: 13,
    minZoom: 10,
    maxZoom: 17,
    layers: [subMapLayers.satellite],
    zoomControl: true
  });

  subMapItemsLayer = L.layerGroup().addTo(subMap);

  // Wire sub-map layer toggle buttons
  document.querySelectorAll(".submap-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".submap-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const chosen = btn.getAttribute("data-sublayer");
      setDetailSubMapLayer(chosen);
    });
  });
}

function setDetailSubMapLayer(layerKey) {
  if (!subMap || !subMapLayers[layerKey] || subMapCurrentLayer === layerKey) return;
  subMap.removeLayer(subMapLayers[subMapCurrentLayer]);
  subMap.addLayer(subMapLayers[layerKey]);
  subMapLayers[layerKey].bringToBack();
  subMapCurrentLayer = layerKey;
}

function openZoneDetailMap(zone, speciesName = "Bolet") {
  currentDetailZone = zone;
  const modal = document.getElementById("detailedMapModal");
  if (!modal) return;

  modal.classList.add("active");

  // Populate headers
  document.getElementById("detailModalZoneName").textContent = zone.name;
  document.getElementById("detailModalSub").textContent =
    `${zone.comarca} (${zone.region}) • ${zone.elevation_m}m • ${zone.forest_type.split("(")[0]}`;

  const tipsText = document.getElementById("detailModalTipsText");
  if (tipsText && zone.explanation) {
    tipsText.textContent = zone.explanation.aspect_detail || "Comprova les fondalades i obagues per a la màxima retenció d'aigua.";
  }

  // Initialize sub-map if first time
  initDetailSubMap();

  // Resize and center after DOM paint
  setTimeout(() => {
    subMap.invalidateSize();
    subMap.setView([zone.lat, zone.lon], 13);
    renderZoneMicroSectors(zone, speciesName);
  }, 100);
}

function closeZoneDetailMap() {
  const modal = document.getElementById("detailedMapModal");
  if (modal) {
    modal.classList.remove("active");
  }
}

function renderZoneMicroSectors(zone, speciesName) {
  if (!subMapItemsLayer) return;
  subMapItemsLayer.clearLayers();

  const baseProb = zone.probability;
  const lat = zone.lat;
  const lon = zone.lon;

  // 1. Perimeter zone circle (1.5 km radius)
  L.circle([lat, lon], {
    radius: 1500,
    color: "#38bdf8",
    weight: 2,
    dashArray: "6, 6",
    fillColor: "#38bdf8",
    fillOpacity: 0.08
  }).addTo(subMapItemsLayer);

  // 2. Center Core Hotspot Marker
  const coreMarker = L.circleMarker([lat, lon], {
    radius: 10,
    fillColor: getProbColor(baseProb),
    color: "#ffffff",
    weight: 3,
    opacity: 1,
    fillOpacity: 0.95
  }).addTo(subMapItemsLayer);

  coreMarker.bindPopup(`
    <div style="font-family: var(--font-family); padding: 4px;">
      <strong style="color: #0f172a; font-size: 13px;">📍 ${zone.name} (Nucli)</strong><br/>
      <span style="color: #475569; font-size: 12px;">Probabilitat base: <strong>${baseProb}%</strong></span><br/>
      <span style="color: #0284c7; font-size: 11px;">Altitud: ${zone.elevation_m}m • ${zone.forest_type.split("(")[0]}</span>
    </div>
  `).openPopup();

  // 3. Micro-Sector Waypoints
  const microSectors = [
    {
      title: "🌲 Obaga Humida (Nord)",
      desc: "Vessant de menor insolació i evaporació. Reté la humitat 2-3 setmanes més.",
      offsetLat: 0.010,
      offsetLon: 0.002,
      prob: Math.min(100, Math.round(baseProb * 1.12)),
      color: "#10b981",
      border: "#6ee7b7"
    },
    {
      title: "☀️ Solana Càlida (Sud)",
      desc: "Major insolació tèrmica. Favorable en setmanes fredes o començament de glaçades.",
      offsetLat: -0.010,
      offsetLon: -0.002,
      prob: Math.max(10, Math.round(baseProb * 0.90)),
      color: "#f59e0b",
      border: "#fcd34d"
    },
    {
      title: "💧 Fons de Vall / Torrent",
      desc: "Acumulació d'aigua d'escorriment superficial i màxima molsa.",
      offsetLat: -0.002,
      offsetLon: 0.009,
      prob: Math.min(100, Math.round(baseProb * 1.15)),
      color: "#3b82f6",
      border: "#93c5fd"
    },
    {
      title: "🏔️ Cota Superior / Carena",
      desc: "Àrea alta més ventilada; atenció al xoc tèrmic nocturn.",
      offsetLat: 0.007,
      offsetLon: -0.008,
      prob: Math.max(10, Math.round(baseProb * 0.86)),
      color: "#a855f7",
      border: "#d8b4fe"
    }
  ];

  microSectors.forEach(sec => {
    const sLat = lat + sec.offsetLat;
    const sLon = lon + sec.offsetLon;

    const marker = L.circleMarker([sLat, sLon], {
      radius: 8,
      fillColor: sec.color,
      color: sec.border,
      weight: 2,
      opacity: 0.95,
      fillOpacity: 0.9
    });

    marker.bindPopup(`
      <div style="font-family: var(--font-family); min-width: 170px; padding: 4px;">
        <strong style="color: #0f172a; font-size: 13px;">${sec.title}</strong><br/>
        <span style="color: ${sec.color}; font-weight: bold; font-size: 12px;">Índex estimat: ${sec.prob}%</span><br/>
        <p style="color: #475569; font-size: 11px; margin: 4px 0 0 0; line-height: 1.3;">${sec.desc}</p>
      </div>
    `);

    subMapItemsLayer.addLayer(marker);
  });
}
