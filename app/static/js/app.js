// Main Application Controller
let state = {
  currentSpecies: "cep",
  speciesList: [],
  forecastData: null,
  activeZoneId: null,
  searchFilter: "",
  comarcaFilter: "",
  inspectorClosed: false
};

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  // Initialize Leaflet map
  initMap(onMapZoneSelect);

  // Setup UI event listeners
  setupEventListeners();

  // Load initial data
  await loadSpecies();
  await loadComarques();
  await loadForecast(state.currentSpecies);
}

function setupEventListeners() {
  // Basemap Selector buttons
  document.querySelectorAll(".basemap-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".basemap-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const layer = btn.getAttribute("data-layer");
      if (typeof setBaseLayer === "function") {
        setBaseLayer(layer);
      }
    });
  });

  // Comarca dropdown
  const comarcaSelect = document.getElementById("comarcaSelect");
  if (comarcaSelect) {
    comarcaSelect.addEventListener("change", (e) => {
      state.comarcaFilter = e.target.value;
      filterAndRenderHotspots();
    });
  }

  // Search input
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      state.searchFilter = e.target.value.toLowerCase();
      filterAndRenderHotspots();
    });
  }

  // Layer toggles
  const chkHeatmap = document.getElementById("chkHeatmap");
  if (chkHeatmap) {
    chkHeatmap.addEventListener("change", (e) => toggleHeatmap(e.target.checked));
  }

  const chkMarkers = document.getElementById("chkMarkers");
  if (chkMarkers) {
    chkMarkers.addEventListener("change", (e) => toggleMarkers(e.target.checked));
  }

  // Refresh Weather button
  const btnRefresh = document.getElementById("btnRefreshWeather");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", handleRefreshWeather);
  }

  // Close & Minimize Inspector drawer
  const btnCloseInspector = document.getElementById("btnCloseInspector");
  const btnOpenInspector = document.getElementById("btnOpenInspector");
  const drawer = document.getElementById("inspectorDrawer");

  if (btnCloseInspector) {
    btnCloseInspector.addEventListener("click", (e) => {
      e.stopPropagation();
      state.inspectorClosed = true;
      drawer.classList.remove("open");
      if (btnOpenInspector) {
        btnOpenInspector.style.display = "flex";
      }
    });
  }

  if (btnOpenInspector) {
    btnOpenInspector.addEventListener("click", (e) => {
      e.stopPropagation();
      state.inspectorClosed = false;
      drawer.classList.add("open");
      btnOpenInspector.style.display = "none";
    });
  }

  // Mobile sidebar drawer toggles
  const btnToggleSidebar = document.getElementById("btnToggleSidebar");
  if (btnToggleSidebar) {
    btnToggleSidebar.addEventListener("click", openSidebar);
  }

  const btnCloseSidebar = document.getElementById("btnCloseSidebar");
  if (btnCloseSidebar) {
    btnCloseSidebar.addEventListener("click", closeSidebar);
  }

  const sidebarBackdrop = document.getElementById("sidebarBackdrop");
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", closeSidebar);
  }

  // Close with Esc key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeSidebar();
      if (drawer && drawer.classList.contains("open")) {
        state.inspectorClosed = true;
        drawer.classList.remove("open");
        if (btnOpenInspector) {
          btnOpenInspector.style.display = "flex";
        }
      }
    }
  });
}

function openSidebar() {
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  if (sidebar) sidebar.classList.add("open");
  if (backdrop) backdrop.classList.add("active");
}

function closeSidebar() {
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  if (sidebar) sidebar.classList.remove("open");
  if (backdrop) backdrop.classList.remove("active");
}

async function loadSpecies() {
  try {
    const res = await fetch("/api/species");
    state.speciesList = await res.json();
    renderSpeciesGrid();
  } catch (err) {
    console.error("Error loading species:", err);
  }
}

function renderSpeciesGrid() {
  const container = document.getElementById("speciesGrid");
  const mobileBar = document.getElementById("mobileSpeciesBar");

  if (container) {
    container.innerHTML = "";
    state.speciesList.forEach(sp => {
      const card = document.createElement("div");
      card.className = `species-card ${sp.id === state.currentSpecies ? "active" : ""}`;
      card.onclick = () => selectSpecies(sp.id);
      card.innerHTML = `
        <div class="species-card-header">
          <span class="species-icon">${sp.icon}</span>
          <div>
            <div class="species-name">${sp.name_ca.split("(")[0]}</div>
            <div class="species-sci">${sp.scientific_name.split("/")[0]}</div>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  }

  if (mobileBar) {
    mobileBar.innerHTML = "";
    state.speciesList.forEach(sp => {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = `mobile-species-pill ${sp.id === state.currentSpecies ? "active" : ""}`;
      pill.onclick = () => selectSpecies(sp.id);
      pill.innerHTML = `<span>${sp.icon}</span> <span>${sp.name_ca.split("(")[0].trim()}</span>`;
      mobileBar.appendChild(pill);
    });
  }
}

function selectSpecies(speciesId) {
  if (state.currentSpecies === speciesId) return;
  state.currentSpecies = speciesId;

  // Re-render species active classes
  renderSpeciesGrid();

  // Reload forecast
  loadForecast(speciesId);
}

async function loadComarques() {
  try {
    const res = await fetch("/api/comarques");
    const comarques = await res.json();
    const select = document.getElementById("comarcaSelect");
    if (!select) return;

    select.innerHTML = `<option value="">Totes les comarques (${comarques.length})</option>`;
    comarques.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Error loading comarques:", err);
  }
}

async function loadForecast(speciesId) {
  showLoader(true);
  try {
    const res = await fetch(`/api/forecast?species_id=${speciesId}`);
    const data = await res.json();
    state.forecastData = data;

    // Update map with new heatmap points and zone circles
    updateMapData(data.zones, data.heatmap_points);

    // Update hotspots list
    filterAndRenderHotspots();

    // If a zone is already active or open the top hotspot
    if (state.activeZoneId) {
      inspectZone(state.activeZoneId);
    } else if (data.zones.length > 0) {
      inspectZone(data.zones[0].zone_id, false);
    }
  } catch (err) {
    console.error("Error loading forecast:", err);
  } finally {
    showLoader(false);
  }
}

function filterAndRenderHotspots() {
  const container = document.getElementById("hotspotList");
  if (!container || !state.forecastData) return;

  container.innerHTML = "";

  let zones = state.forecastData.zones;

  // Apply comarca filter
  if (state.comarcaFilter) {
    zones = zones.filter(z => z.comarca.toLowerCase() === state.comarcaFilter.toLowerCase());
  }

  // Apply search text
  if (state.searchFilter) {
    zones = zones.filter(z =>
      z.name.toLowerCase().includes(state.searchFilter) ||
      z.comarca.toLowerCase().includes(state.searchFilter) ||
      z.forest_type.toLowerCase().includes(state.searchFilter)
    );
  }

  // Display top spots (limit to 12 for clean sidebar)
  const displayZones = zones.slice(0, 15);

  if (displayZones.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 20px;">No s'han trobat zones que coincideixin.</div>`;
    return;
  }

  displayZones.forEach(z => {
    const item = document.createElement("div");
    item.className = "hotspot-item";
    item.onclick = () => {
      if (window.innerWidth <= 768) {
        closeSidebar();
      }
      flyToCoordinates(z.lat, z.lon, 11);
      inspectZone(z.zone_id);
    };

    const badgeBg = getProbBadgeStyle(z.probability);

    item.innerHTML = `
      <div class="hotspot-info">
        <h4>${z.name}</h4>
        <div class="hotspot-meta">
          <span>📍 ${z.comarca}</span>
          <span>🏔️ ${z.elevation_m}m</span>
          <span>🌲 ${z.forest_type.split("(")[0]}</span>
        </div>
      </div>
      <div class="badge-prob" style="${badgeBg}">
        ${z.probability}%
      </div>
    `;

    container.appendChild(item);
  });
}

function onMapZoneSelect(zoneId, lat, lon) {
  if (zoneId) {
    state.inspectorClosed = false;
    inspectZone(zoneId);
  } else if (lat && lon) {
    // If user clicked on the map, only auto-inspect if drawer was not explicitly closed
    if (!state.inspectorClosed) {
      fetchNearestZone(lat, lon);
    }
  }
}

async function fetchNearestZone(lat, lon) {
  try {
    const res = await fetch(`/api/nearest-zone?lat=${lat}&lon=${lon}&species_id=${state.currentSpecies}`);
    if (res.ok) {
      const zoneData = await res.json();
      renderZoneDetails(zoneData);
      flyToCoordinates(zoneData.lat, zoneData.lon, 10);
    }
  } catch (err) {
    console.error("Error fetching nearest zone:", err);
  }
}

async function inspectZone(zoneId, doFly = true) {
  state.activeZoneId = zoneId;
  try {
    const res = await fetch(`/api/zone/${zoneId}?species_id=${state.currentSpecies}`);
    if (res.ok) {
      const zoneData = await res.json();
      renderZoneDetails(zoneData);
      if (doFly) {
        flyToCoordinates(zoneData.lat, zoneData.lon, 11);
      }
    }
  } catch (err) {
    console.error("Error inspecting zone:", err);
  }
}

function renderZoneDetails(zone) {
  const drawer = document.getElementById("inspectorDrawer");
  if (!drawer) return;

  // Open drawer and hide the reopen tab
  state.inspectorClosed = false;
  drawer.classList.add("open");
  const btnOpenInspector = document.getElementById("btnOpenInspector");
  if (btnOpenInspector) {
    btnOpenInspector.style.display = "none";
  }

  // Header Info
  document.getElementById("inspZoneName").textContent = zone.name;
  document.getElementById("inspComarca").textContent = `📍 ${zone.comarca} (${zone.region})`;
  document.getElementById("inspElevation").textContent = `🏔️ ${zone.elevation_m} m`;
  document.getElementById("inspForest").textContent = `🌲 ${zone.forest_type}`;
  document.getElementById("inspAspect").textContent = `🌓 ${zone.aspect}`;
  document.getElementById("inspSoil").textContent = `🪨 Sòl ${zone.soil_type}`;

  // Big Probability Meter
  const probVal = zone.probability;
  const probCircle = document.getElementById("inspProbCircle");
  probCircle.style.background = getProbColor(probVal);
  document.getElementById("inspProbNum").textContent = `${probVal}%`;
  document.getElementById("inspRatingLabel").textContent = zone.rating_label;
  document.getElementById("inspSpeciesName").textContent = `Probabilitat per a: ${state.forecastData ? state.forecastData.species.name_ca : 'Bolet'}`;

  // Natural Language Summary
  const expl = zone.explanation;
  if (expl) {
    document.getElementById("inspSummary").textContent = expl.summary_ca;
    document.getElementById("inspRainDetail").textContent = expl.rain_detail;
    document.getElementById("inspSoilDetail").textContent = expl.soil_detail;
    document.getElementById("inspTempDetail").textContent = expl.temp_detail;
    document.getElementById("inspHabitatDetail").textContent = expl.habitat_detail;
    document.getElementById("inspAspectDetail").textContent = expl.aspect_detail;
    document.getElementById("inspForagerTips").textContent = expl.forager_tips;
    document.getElementById("inspToxicityWarning").textContent = expl.toxicity_warning;
  }

  // Factor Progress Bars
  const f = zone.factors;
  setBar("barRain", f.rain_score, `${f.rain_score}/100 (${f.rain_14d_mm} mm en 14d)`);
  setBar("barSoil", f.soil_score, `${f.soil_score}/100 (${f.soil_moisture_pct}%)`);
  setBar("barTemp", f.temp_score, `${f.temp_score}/100 (${f.temp_mean_c}°C mitjana)`);
  setBar("barHabitat", f.habitat_score, `${f.habitat_score}/100`);
  setBar("barElevation", f.elevation_score, `${f.elevation_score}/100`);
  setBar("barAspect", f.aspect_score, `${f.aspect_score}/100`);

  // Render 14-day history chart
  renderWeatherChart(zone.history);
}

function setBar(elementId, score, labelText) {
  const bar = document.getElementById(elementId);
  const label = document.getElementById(`${elementId}Label`);
  if (bar) {
    bar.style.width = `${Math.min(100, Math.max(3, score))}%`;
    bar.style.backgroundColor = getProbColor(score);
  }
  if (label) {
    label.textContent = labelText;
  }
}

async function handleRefreshWeather() {
  const btn = document.getElementById("btnRefreshWeather");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳</span> <span>Actualitzant...</span>`;
  }
  try {
    const res = await fetch("/api/weather/refresh", { method: "POST" });
    if (res.ok) {
      await loadForecast(state.currentSpecies);
      alert("✅ Dades meteorològiques d'Open-Meteo actualitzades correctament!");
    }
  } catch (err) {
    alert("⚠️ No s'han pogut actualitzar les dades meteorològiques en viu.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>🔄</span> <span>Actualitza Dades (Open-Meteo)</span>`;
    }
  }
}

function getProbBadgeStyle(prob) {
  const color = getProbColor(prob);
  return `background: ${color}20; color: ${color}; border: 1px solid ${color}50;`;
}

function showLoader(show) {
  const loader = document.getElementById("appLoader");
  if (loader) {
    loader.style.display = show ? "flex" : "none";
  }
}

