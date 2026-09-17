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
    topo: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
      attribution: '&copy; Esri Topo',
      maxZoom: 18
    }),
    satellite: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      attribution: '&copy; Esri Satèl·lit',
      maxZoom: 18
    })
  };

  subMapCurrentLayer = "topo";

  subMap = L.map("detailSubMap", {
    center: [41.78, 1.85],
    zoom: 13,
    minZoom: 10,
    maxZoom: 17,
    layers: [subMapLayers.topo],
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

function openZoneDetailMap(zone, speciesObj) {
  currentDetailZone = zone;
  const modal = document.getElementById("detailedMapModal");
  if (!modal) return;

  modal.classList.add("active");

  // Populate headers
  document.getElementById("detailModalZoneName").textContent = zone.name;
  document.getElementById("detailModalSub").textContent =
    `${zone.comarca} (${zone.region}) • Cota central: ${zone.elevation_m}m • Bosc: ${zone.forest_type.split("(")[0]}`;

  // Initialize sub-map if first time
  initDetailSubMap();

  // Resize and center after DOM paint
  setTimeout(() => {
    subMap.invalidateSize();
    subMap.setView([zone.lat, zone.lon], 13);
    renderZoneDetailedMap(zone, speciesObj);
    renderAltitudeAssessment(zone, speciesObj);
  }, 100);
}

function closeZoneDetailMap() {
  const modal = document.getElementById("detailedMapModal");
  if (modal) {
    modal.classList.remove("active");
  }
}

function renderZoneDetailedMap(zone, speciesObj) {
  if (!subMapItemsLayer) return;
  subMapItemsLayer.clearLayers();

  const baseProb = zone.probability;
  const lat = zone.lat;
  const lon = zone.lon;

  // 1. Perimeter zone envelope (1.5 km radius)
  L.circle([lat, lon], {
    radius: 1500,
    color: "#38bdf8",
    weight: 2,
    dashArray: "6, 6",
    fillColor: "#38bdf8",
    fillOpacity: 0.06
  }).addTo(subMapItemsLayer);

  // 2. Real central massif location pin
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
      <strong style="color: #0f172a; font-size: 13px;">📍 ${zone.name}</strong><br/>
      <span style="color: #475569; font-size: 12px;">Cota de referència: <strong>${zone.elevation_m}m</strong></span><br/>
      <span style="color: #0284c7; font-size: 11px;">${zone.forest_type.split("(")[0]} • ${zone.aspect}</span>
    </div>
  `).openPopup();
}

function renderAltitudeAssessment(zone, speciesObj) {
  const elevContainer = document.getElementById("detailAltitudeTiers");
  const altSub = document.getElementById("detailAltSubtitle");
  const tactSub = document.getElementById("detailTacticalSubtitle");
  const tactText = document.getElementById("detailTacticalAdviceText");

  const species = (speciesObj && speciesObj.optimal_elevation_m) ? speciesObj : {
    name_ca: "Espècie seleccionada",
    elevation_min_m: 500,
    elevation_max_m: 1900,
    optimal_elevation_m: [800, 1600]
  };

  if (altSub) {
    altSub.textContent = `Franja òptima de ${species.name_ca.split("(")[0].trim()}: ${species.optimal_elevation_m[0]}m – ${species.optimal_elevation_m[1]}m (Límit: ${species.elevation_min_m}m – ${species.elevation_max_m}m)`;
  }

  const zoneElev = zone.elevation_m;
  const tempMean = zone.factors ? zone.factors.temp_mean_c : 14.0;
  const rain14d = zone.factors ? zone.factors.rain_14d_mm : 40.0;
  const soilMoist = zone.factors ? zone.factors.soil_moisture_pct : 30;

  const lowElev = Math.max(120, Math.round(zoneElev - 320));
  const midElev = zoneElev;
  const highElev = Math.round(zoneElev + 320);

  // --- 1. ALTITUDE TIERS EVALUATION ---
  if (elevContainer) {
    elevContainer.innerHTML = "";

    const lowTemp = (tempMean + 2.1).toFixed(1);
    const midTemp = tempMean.toFixed(1);
    const highTemp = (tempMean - 2.1).toFixed(1);

    const tiers = [
      {
        name: "Cota Baixa / Peu de massís",
        elev: `${lowElev} m`,
        temp: `${lowTemp}°C`,
        statusClass: (lowElev >= species.optimal_elevation_m[0] && lowElev <= species.optimal_elevation_m[1]) ? "alt-optimal" :
                     (lowElev >= species.elevation_min_m && lowElev <= species.elevation_max_m) ? "alt-favorable" : "alt-marginal",
        statusText: (lowElev >= species.optimal_elevation_m[0] && lowElev <= species.optimal_elevation_m[1]) ? `Òptima (${lowTemp}°C)` :
                    (lowElev >= species.elevation_min_m && lowElev <= species.elevation_max_m) ? `Acceptable (${lowTemp}°C)` : `Fora de rang (${lowTemp}°C)`,
        desc: lowElev < species.elevation_min_m ? "Altitud massa baixa per a aquesta espècie de muntanya." : "Més càlida (+2°C). Idònia si fa fred a dalt o tard a la tardor."
      },
      {
        name: "Cota Mitjana (Cota Central)",
        elev: `${midElev} m`,
        temp: `${midTemp}°C`,
        statusClass: (midElev >= species.optimal_elevation_m[0] && midElev <= species.optimal_elevation_m[1]) ? "alt-optimal" :
                     (midElev >= species.elevation_min_m && midElev <= species.elevation_max_m) ? "alt-favorable" : "alt-marginal",
        statusText: (midElev >= species.optimal_elevation_m[0] && midElev <= species.optimal_elevation_m[1]) ? `Òptima (${midTemp}°C)` :
                    (midElev >= species.elevation_min_m && midElev <= species.elevation_max_m) ? `Favorable (${midTemp}°C)` : `Marginal (${midTemp}°C)`,
        desc: "Nucli de la zona. Concentra la massa forestal de referència."
      },
      {
        name: "Cota Alta / Carenes",
        elev: `${highElev} m`,
        temp: `${highTemp}°C`,
        statusClass: (highTemp < 4.0) ? "alt-marginal" :
                     (highElev >= species.optimal_elevation_m[0] && highElev <= species.optimal_elevation_m[1]) ? "alt-optimal" :
                     (highElev >= species.elevation_min_m && highElev <= species.elevation_max_m) ? "alt-favorable" : "alt-marginal",
        statusText: (highTemp < 4.0) ? `Risc gelada (${highTemp}°C)` :
                    (highElev >= species.optimal_elevation_m[0] && highElev <= species.optimal_elevation_m[1]) ? `Òptima (${highTemp}°C)` : `Freda (${highTemp}°C)`,
        desc: highTemp < 4.0 ? "Ventilació forta i baixes temperatures nocturnes que frenen el miceli." : "Ambient frescal d'altura."
      }
    ];

    tiers.forEach(t => {
      const item = document.createElement("div");
      item.className = "alt-tier-item";
      item.innerHTML = `
        <div class="alt-tier-label">
          <div class="alt-tier-name">${t.name} <span class="alt-tier-elev">(${t.elev})</span></div>
          <div style="font-size: 0.7rem; color: #94a3b8;">${t.desc}</div>
        </div>
        <div class="alt-tier-status ${t.statusClass}">${t.statusText}</div>
      `;
      elevContainer.appendChild(item);
    });
  }

  // --- 2. TACTICAL FORAGING ADVICE ---
  if (tactSub) {
    tactSub.textContent = `Estratègia altitudinal per a ${zone.name}`;
  }

  if (tactText) {
    let advice = "";
    if (rain14d < 35) {
      advice = `La pluja acumulada en 14 dies ha estat modesta (${rain14d} mm). Per maximitzar les opcions de trobada, <strong>centra la cerca a la cota mitjana-baixa (~${Math.max(lowElev, species.optimal_elevation_m[0])}m)</strong> en zones forestals denses de ${zone.forest_type.split("(")[0].trim()} on la molsa retingui la humitat del sòl.`;
    } else if (tempMean < 8.0) {
      advice = `Les temperatures a cotes altes són molt fredes (${tempMean}°C de mitjana) amb risc de terra refredat. Recomanem <strong>descendir cap a la cota baixa (~${Math.max(lowElev, species.elevation_min_m)}m)</strong> cercant replans arrecerats amb temperatures més suaus.`;
    } else {
      advice = `Aquest massís compta amb un excel·lent equilibri de pluja (${rain14d} mm) i temperatura (${tempMean}°C). L'espècie es troba en plena franja de producció a la <strong>cota mitjana (${zoneElev}m)</strong> dins del bosc de ${zone.forest_type.split("(")[0].trim()}.`;
    }
    tactText.innerHTML = advice;
  }
}
