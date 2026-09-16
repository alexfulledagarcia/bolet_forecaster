// Weather History Chart Handler using Chart.js
let weatherChartInstance = null;

function renderWeatherChart(historyData) {
  const canvas = document.getElementById("weatherChart");
  if (!canvas) return;

  if (weatherChartInstance) {
    weatherChartInstance.destroy();
    weatherChartInstance = null;
  }

  if (!historyData || historyData.length === 0) {
    return;
  }

  const labels = historyData.map(d => {
    // Format date MM-DD
    const parts = d.date.split("-");
    return parts.length >= 3 ? `${parts[2]}/${parts[1]}` : d.date;
  });

  const precip = historyData.map(d => d.precipitation_mm);
  const tempMax = historyData.map(d => d.temp_max_c);
  const tempMin = historyData.map(d => d.temp_min_c);

  const ctx = canvas.getContext("2d");

  weatherChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Pluja (mm)",
          data: precip,
          backgroundColor: "rgba(59, 130, 246, 0.65)",
          borderColor: "rgba(59, 130, 246, 1)",
          borderWidth: 1,
          yAxisID: "yRain",
          order: 2
        },
        {
          label: "T. Màxima (°C)",
          data: tempMax,
          type: "line",
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
          yAxisID: "yTemp",
          order: 1
        },
        {
          label: "T. Mínima (°C)",
          data: tempMin,
          type: "line",
          borderColor: "#06b6d4",
          backgroundColor: "transparent",
          borderWidth: 2,
          borderDash: [3, 3],
          pointRadius: 2,
          tension: 0.3,
          yAxisID: "yTemp",
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: "#94a3b8",
            font: { size: 10 }
          }
        },
        tooltip: {
          backgroundColor: "rgba(19, 31, 51, 0.95)",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "#233554",
          borderWidth: 1
        }
      },
      scales: {
        x: {
          ticks: {
            color: "#64748b",
            font: { size: 9 },
            maxRotation: 45
          },
          grid: {
            color: "rgba(255, 255, 255, 0.05)"
          }
        },
        yRain: {
          type: "linear",
          position: "left",
          title: {
            display: true,
            text: "Pluja (mm)",
            color: "#60a5fa",
            font: { size: 10 }
          },
          ticks: { color: "#64748b", font: { size: 9 } },
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          min: 0
        },
        yTemp: {
          type: "linear",
          position: "right",
          title: {
            display: true,
            text: "Temp (°C)",
            color: "#f59e0b",
            font: { size: 10 }
          },
          ticks: { color: "#64748b", font: { size: 9 } },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

