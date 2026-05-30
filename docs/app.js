/* ============================================================
   AireBA Trends — app.js
   Carga de datos, filtros, gráficos (Plotly), mapa (Leaflet),
   tabla de anomalías. Toda la lógica de rendering vive acá.
   ============================================================ */
(function () {
  "use strict";

  /* ---------- estado ---------- */
  const STATE = {
    data: null,
    filters: { station: "All", pollutant: "NO2", year: "All", severity: "All" },
    topN: 20,
    sort: { key: "date", dir: "desc" },
  };

  const POLLUTANTS = ["NO2", "CO", "PM10"];
  const POL_LABEL = { NO2: "NO₂", CO: "CO", PM10: "PM10" };
  const MONTHS_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];

  /* ---------- helpers ---------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const cssvar = (n) => getComputedStyle(document.body).getPropertyValue(n).trim();
  const polColor = (p) => cssvar("--" + p.toLowerCase());
  const polSoft = (p) => cssvar("--" + p.toLowerCase() + "-soft");
  const STATION_COLOR = () => ({ Centenario: cssvar("--pm10"), "Córdoba": cssvar("--no2"), "La Boca": cssvar("--co"), Palermo: cssvar("--brand") });
  const normalizeStationName = (value) => {
    const station = String(value || "").trim().toLowerCase();
    if (station === "centenario") return "Centenario";
    if (station === "cordoba" || station === "córdoba") return "Córdoba";
    if (station === "la_boca" || station === "la boca") return "La Boca";
    if (station === "palermo") return "Palermo";
    return String(value || "").trim();
  };
  const stationList = () => [...new Set((STATE.data?.stations || []).map((s) => normalizeStationName(s.station)))];
  const stationColor = (station) => STATION_COLOR()[normalizeStationName(station)] || cssvar("--brand");

  function formatNumber(n, dec) {
    if (n == null || isNaN(n)) return "—";
    return new Intl.NumberFormat("es-AR", { minimumFractionDigits: dec ?? 0, maximumFractionDigits: dec ?? 0 }).format(n);
  }
  function formatDate(iso) {
    if (!iso) return "—";
    const normalized = normalizeDateValue(iso);
    const [y, m, d] = normalized.split("-").map(Number);
    return `${d} ${MONTHS_ES[m - 1].toLowerCase()} ${y}`;
  }
  function normalizeDateValue(value) {
    if (typeof value === "number") return new Date(value).toISOString().slice(0, 10);
    if (typeof value === "string" && value.includes("T")) return value.slice(0, 10);
    return String(value || "");
  }
  function unitOf(p) {
    const direct = STATE.data?.metadata?.units?.[p];
    if (direct) return direct;
    const pollutantMeta = (STATE.data?.metadata?.pollutants || []).find((item) => item.pollutant === p);
    return pollutantMeta?.unit || "";
  }

  /* ---------- carga ---------- */
  // Lee los JSON estáticos preprocesados desde ./data/ (GitHub Pages).
  async function loadJson(path) {
    try {
      const response = await fetch(path);
      if (!response.ok) throw new Error(`No se pudo cargar ${path}`);
      return await response.json();
    } catch (err) {
      console.error(err);
      showErrorMessage("No se pudieron cargar los datos.");
      return null;
    }
  }
  async function loadAllData() {
    const [summary, metadata, stations, yearly, monthly, anomalies] = await Promise.all([
      loadJson("./data/summary.json"),
      loadJson("./data/metadata.json"),
      loadJson("./data/stations.json"),
      loadJson("./data/yearly_trends.json"),
      loadJson("./data/monthly_trends.json"),
      loadJson("./data/anomalies.json"),
    ]);
    if (!summary || !yearly || !monthly || !anomalies || !stations) return false;
    STATE.data = {
      summary,
      metadata,
      stations: stations.map((station) => ({ ...station, station: normalizeStationName(station.station) })),
      yearly_trends: yearly.map((row) => ({ ...row, station: normalizeStationName(row.station) })),
      monthly_trends: monthly.map((row) => ({ ...row, station: normalizeStationName(row.station) })),
      anomalies: anomalies.map((row) => ({ ...row, station: normalizeStationName(row.station), date: normalizeDateValue(row.date) })),
    };
    return true;
  }

  function showErrorMessage(msg) {
    let t = $("#errToast");
    if (!t) {
      t = document.createElement("div");
      t.id = "errToast"; t.className = "err-toast";
      t.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg><span></span>`;
      document.body.appendChild(t);
    }
    t.querySelector("span").textContent = msg;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 4200);
  }

  /* ============================================================
     Summary cards
     ============================================================ */
  function renderSummaryCards() {
    const s = STATE.data.summary;
    const set = (id, html) => { const el = $(id); if (el) el.innerHTML = html; };
    set("#sumPeriod", `${s.period_start}<small> – </small>${s.period_end}`);
    set("#sumLatest", `${formatDate(s.latest_available_date).replace(/ \d{4}$/, "")}<small> ${s.latest_available_date.slice(0,4)}</small>`);
    set("#sumPollutants", `${s.pollutants.length}`);
    set("#sumStations", `${s.stations_count}`);
    set("#sumRecords", abbr(s.total_records));
    set("#sumAnoms", formatNumber(s.anomalies_detected));
  }
  function abbr(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(2).replace(/\.?0+$/, "") + "<small> M</small>";
    if (n >= 1e3) return (n / 1e3).toFixed(0) + "<small> mil</small>";
    return formatNumber(n);
  }

  /* ============================================================
     Filtros
     ============================================================ */
  function renderFilters() {
    renderHeroPollutantChips();
    // pollutant segmented
    const polSeg = $("#fPollutant");
    polSeg.innerHTML = POLLUTANTS.map(p =>
      `<button data-v="${p}" aria-pressed="${p === STATE.filters.pollutant}">
         <span class="sw" style="background:${polColor(p)}"></span>${POL_LABEL[p]}
       </button>`).join("");
    polSeg.onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      STATE.filters.pollutant = b.dataset.v;
      $$("button", polSeg).forEach(x => x.setAttribute("aria-pressed", x === b));
      applyFilters();
    };

    // station select
    const stSel = $("#fStation");
    stSel.innerHTML = `<option value="All">Todas las estaciones</option>` +
      stationList().map(s => `<option value="${s}">${s}</option>`).join("");
    stSel.value = STATE.filters.station;
    stSel.onchange = () => { STATE.filters.station = stSel.value; applyFilters(); };

    // year select
    const yrSel = $("#fYear");
    const years = []; for (let y = STATE.data.summary.period_end; y >= STATE.data.summary.period_start; y--) years.push(y);
    yrSel.innerHTML = `<option value="All">Todos los años</option>` + years.map(y => `<option value="${y}">${y}</option>`).join("");
    yrSel.value = STATE.filters.year;
    yrSel.onchange = () => { STATE.filters.year = yrSel.value; applyFilters(); };

    // severity segmented
    const sevSeg = $("#fSeverity");
    const sevs = [["All","Todas"],["Moderate","Moderada"],["High","Alta"],["Extreme","Extrema"]];
    sevSeg.innerHTML = sevs.map(([v,l]) =>
      `<button data-v="${v}" aria-pressed="${v === STATE.filters.severity}">${l}</button>`).join("");
    sevSeg.onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      STATE.filters.severity = b.dataset.v;
      $$("button", sevSeg).forEach(x => x.setAttribute("aria-pressed", x === b));
      applyFilters();
    };

    $("#resetFilters").onclick = () => {
      STATE.filters = { station: "All", pollutant: "NO2", year: "All", severity: "All" };
      renderFilters(); applyFilters();
    };
  }

  function applyFilters() {
    renderHero();
    renderHeroPollutantChips();
    updateActiveContext();
    renderYearlyChart();
    renderMonthlyChart();
    renderAnomaliesTable();
    renderAnomaliesChart();
    highlightMapPollutant();
  }

  function updateActiveContext() {
    const f = STATE.filters;
    const parts = [];
    parts.push(f.station === "All" ? "todas las estaciones" : f.station);
    parts.push(POL_LABEL[f.pollutant]);
    if (f.year !== "All") parts.push(f.year);
    $("#ctxYearly") && ($("#ctxYearly").textContent = `${POL_LABEL[f.pollutant]} · ${f.station === "All" ? "4 estaciones" : f.station}`);
    $("#ctxMonthly") && ($("#ctxMonthly").textContent = `${POL_LABEL[f.pollutant]} · ${f.station === "All" ? "promedio ciudad" : f.station}`);
  }

  /* ============================================================
     Plotly base
     ============================================================ */
  const PCONFIG = { responsive: true, displayModeBar: false };
  function baseLayout() {
    const mut = cssvar("--text-mut"), grid = cssvar("--border"), faint = cssvar("--text-faint"), surf = cssvar("--surface");
    return {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Hanken Grotesk, system-ui, sans-serif", color: mut, size: 13 },
      margin: { l: 56, r: 22, t: 14, b: 44 },
      xaxis: { gridcolor: grid, zerolinecolor: grid, linecolor: grid, tickcolor: grid, color: faint, automargin: true },
      yaxis: { gridcolor: grid, zerolinecolor: grid, linecolor: grid, tickcolor: grid, color: faint, automargin: true },
      hoverlabel: { bgcolor: surf, bordercolor: grid, font: { family: "Hanken Grotesk, sans-serif", color: cssvar("--text"), size: 13 } },
      legend: { orientation: "h", y: 1.12, x: 0, font: { size: 12.5 }, bgcolor: "rgba(0,0,0,0)" },
      showlegend: false,
    };
  }

  /* ============================================================
     5.4 Yearly trends
     ============================================================ */
  function renderYearlyChart() {
    const f = STATE.filters;
    const sc = STATION_COLOR();
    const rows = STATE.data.yearly_trends.filter(d => d.pollutant === f.pollutant);
    const stations = f.station === "All" ? stationList() : [f.station];
    const traces = [];
    stations.forEach(st => {
      const sr = rows.filter(d => d.station === st).sort((a, b) => a.year - b.year);
      if (!sr.length) return;
      // min-max band only when a single station is selected
      if (stations.length === 1) {
        traces.push({
          x: sr.map(d => d.year).concat(sr.map(d => d.year).reverse()),
          y: sr.map(d => d.max_value).concat(sr.map(d => d.min_value).reverse()),
          fill: "toself", fillcolor: hexA(stationColor(st), .10), line: { width: 0 },
          hoverinfo: "skip", showlegend: false, type: "scatter",
        });
      }
      traces.push({
        x: sr.map(d => d.year), y: sr.map(d => d.avg_value),
        mode: "lines+markers", name: st, type: "scatter",
        line: { color: stationColor(st), width: 2.6, shape: "spline", smoothing: .6 },
        marker: { color: stationColor(st), size: 5.5, line: { color: cssvar("--surface"), width: 1.5 } },
        hovertemplate: `<b>${st}</b><br>%{x} · %{y:.1f} ${unitOf(f.pollutant)}<extra></extra>`,
      });
    });
    const lay = baseLayout();
    lay.showlegend = false;
    lay.yaxis.title = { text: `${POL_LABEL[f.pollutant]} promedio anual (${unitOf(f.pollutant)})`, font: { size: 12, color: cssvar("--text-faint") }, standoff: 12 };
    lay.xaxis.dtick = 2;
    Plotly.react("chartYearly", traces, lay, PCONFIG);
    renderYearlyLegend(stations, sc);
  }
  function renderYearlyLegend(stations, sc) {
    const el = $("#legendYearly"); if (!el) return;
    el.innerHTML = stations.map(s => `<span class="li"><i style="background:${stationColor(s)}"></i>${s}</span>`).join("");
  }

  /* ============================================================
     5.5 Monthly trends — heatmap año × mes
     ============================================================ */
  function renderMonthlyChart() {
    const f = STATE.filters;
    let rows = STATE.data.monthly_trends.filter(d => d.pollutant === f.pollutant);
    if (f.station !== "All") rows = rows.filter(d => d.station === f.station);
    const years = []; for (let y = STATE.data.summary.period_start; y <= STATE.data.summary.period_end; y++) years.push(y);
    // z[month][year] = avg across stations
    const acc = {}; // key year-month -> {sum,n}
    rows.forEach(d => { const k = d.year + "-" + d.month; (acc[k] = acc[k] || { s: 0, n: 0 }); acc[k].s += d.avg_value; acc[k].n++; });
    const z = MONTHS_ES.map((_, mi) => years.map(y => { const a = acc[y + "-" + (mi + 1)]; return a ? a.s / a.n : null; }));
    const col = polColor(f.pollutant);
    const lay = baseLayout();
    lay.margin = { l: 46, r: 16, t: 10, b: 44 };
    lay.yaxis.gridcolor = "rgba(0,0,0,0)"; lay.xaxis.dtick = 2; lay.xaxis.gridcolor = "rgba(0,0,0,0)";
    lay.yaxis.autorange = "reversed";
    const trace = {
      type: "heatmap", x: years, y: MONTHS_ES, z,
      xgap: 2, ygap: 2,
      colorscale: [[0, hexA(col, .07)], [0.5, hexA(col, .5)], [1, col]],
      hoverongaps: false,
      colorbar: { thickness: 10, len: .85, outlinewidth: 0, tickfont: { size: 11, color: cssvar("--text-faint") }, title: { text: unitOf(f.pollutant), font: { size: 11, color: cssvar("--text-faint") } } },
      hovertemplate: `%{y} %{x}<br><b>%{z:.1f} ${unitOf(f.pollutant)}</b><extra></extra>`,
    };
    Plotly.react("chartMonthly", [trace], lay, PCONFIG);
  }

  /* ============================================================
     5.6 Anomalies table
     ============================================================ */
  function filteredAnomalies() {
    const f = STATE.filters;
    return STATE.data.anomalies.filter(a =>
      (f.station === "All" || a.station === f.station) &&
      (a.pollutant === f.pollutant) &&
      (f.year === "All" || a.date.slice(0, 4) === String(f.year)) &&
      (f.severity === "All" || a.severity === f.severity)
    );
  }
  const SEV_ORDER = { Moderate: 1, High: 2, Extreme: 3 };
  function renderAnomaliesTable() {
    const all = filteredAnomalies();
    const { key, dir } = STATE.sort;
    const sorted = [...all].sort((a, b) => {
      let av = a[key], bv = b[key];
      if (key === "severity") { av = SEV_ORDER[av]; bv = SEV_ORDER[bv]; }
      if (key === "date") { av = a.date; bv = b.date; }
      if (av < bv) return dir === "asc" ? -1 : 1;
      if (av > bv) return dir === "asc" ? 1 : -1;
      return 0;
    });
    const rows = sorted.slice(0, STATE.topN);
    const tb = $("#anomBody");
    const sevLabel = { Normal: "Normal", Moderate: "Moderada", High: "Alta", Extreme: "Extrema" };
    if (!rows.length) {
      tb.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:38px;color:var(--text-faint)">Sin anomalías para estos filtros.</td></tr>`;
    } else {
      tb.innerHTML = rows.map(a => `
        <tr>
          <td class="date">${formatDate(a.date)}</td>
          <td>${a.station}</td>
          <td><span class="pol-tag"><span class="sw" style="background:${polColor(a.pollutant)}"></span>${POL_LABEL[a.pollutant]}</span></td>
          <td class="num">${formatNumber(a.actual_value, a.pollutant === "CO" ? 2 : 1)}</td>
          <td class="num">${formatNumber(a.expected_value, a.pollutant === "CO" ? 2 : 1)}</td>
          <td class="num pct-up">+${formatNumber(a.percentage_difference, 1)}%</td>
          <td class="num">${formatNumber(a.z_score, 2)}</td>
          <td><span class="sev ${a.severity}"><span class="sw"></span>${sevLabel[a.severity]}</span></td>
          <td class="method-cell">${a.method}</td>
        </tr>`).join("");
    }
    $("#anomCount").textContent = `${all.length} anomalías coinciden · mostrando top ${Math.min(STATE.topN, all.length)}`;
    // header sort indicators
    $$("#anomTable thead th.sortable").forEach(th => {
      if (th.dataset.key === key) { th.setAttribute("data-sorted", dir); th.querySelector(".arr").textContent = dir === "asc" ? "▲" : "▼"; }
      else { th.removeAttribute("data-sorted"); th.querySelector(".arr").textContent = "▼"; }
    });
  }

  /* ============================================================
     5.7 Anomalies charts (2)
     ============================================================ */
  function renderAnomaliesChart() {
    renderAnomCountChart();
    renderAnomTopChart();
  }
  function renderAnomCountChart() {
    const f = STATE.filters;
    let rows = STATE.data.anomalies.filter(a =>
      (f.station === "All" || a.station === f.station) &&
      (f.severity === "All" || a.severity === f.severity));
    const years = []; for (let y = STATE.data.summary.period_start; y <= STATE.data.summary.period_end; y++) years.push(y);
    const traces = POLLUTANTS.map(p => ({
      type: "bar", name: POL_LABEL[p],
      x: years, y: years.map(y => rows.filter(a => a.pollutant === p && +normalizeDateValue(a.date).slice(0, 4) === y).length),
      marker: { color: polColor(p) },
      hovertemplate: `<b>${POL_LABEL[p]}</b> · %{x}<br>%{y} anomalías<extra></extra>`,
    }));
    const lay = baseLayout();
    lay.barmode = "stack"; lay.showlegend = true; lay.xaxis.dtick = 2;
    lay.yaxis.title = { text: "Anomalías por año", font: { size: 12, color: cssvar("--text-faint") }, standoff: 12 };
    Plotly.react("chartAnomCount", traces, lay, PCONFIG);
  }
  function renderAnomTopChart() {
    const all = filteredAnomalies();
    const top = [...all].sort((a, b) => b.percentage_difference - a.percentage_difference).slice(0, 15).reverse();
    const lay = baseLayout();
    lay.margin = { l: 150, r: 26, t: 10, b: 40 };
    lay.xaxis.title = { text: "Diferencia vs. esperado (%)", font: { size: 12, color: cssvar("--text-faint") }, standoff: 10 };
    lay.yaxis.gridcolor = "rgba(0,0,0,0)";
    const trace = {
      type: "bar", orientation: "h",
      y: top.map(a => `${a.station} · ${normalizeDateValue(a.date).slice(5)}`),
      x: top.map(a => a.percentage_difference),
      marker: { color: top.map(a => polColor(a.pollutant)) },
      text: top.map(a => "+" + a.percentage_difference.toFixed(0) + "%"),
      textposition: "outside", textfont: { size: 11, color: cssvar("--text-mut"), family: "Space Mono, monospace" },
      cliponaxis: false,
      hovertemplate: top.map(a => `<b>${a.station}</b> · ${formatDate(a.date)}<br>${POL_LABEL[a.pollutant]} · +${a.percentage_difference}% · z=${a.z_score}<extra></extra>`),
    };
    if (!top.length) { Plotly.react("chartAnomTop", [], lay, PCONFIG); return; }
    Plotly.react("chartAnomTop", [trace], lay, PCONFIG);
  }

  /* ============================================================
     5.8 Stations map (Leaflet)
     ============================================================ */
  let MAP, TILE, MARKERS = [];
  const TILES = {
    light: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  };
  function renderStationsMap() {
    if (typeof L === "undefined") return;
    MAP = L.map("map", { scrollWheelZoom: false, zoomControl: true, attributionControl: true }).setView([-34.605, -58.41], 12);
    TILE = L.tileLayer(TILES[currentTheme()], {
      maxZoom: 19, subdomains: "abcd",
      attribution: '&copy; OpenStreetMap &copy; CARTO',
    }).addTo(MAP);
    const sc = STATION_COLOR();
    STATE.data.stations.forEach(s => {
      const color = stationColor(s.station);
      const m = L.circleMarker([s.latitude, s.longitude], {
        radius: 11, color: "#fff", weight: 2, fillColor: color, fillOpacity: 1,
      }).addTo(MAP);
      m._station = s.station;
      const pols = s.pollutants.map(p => `<span class="pp" style="background:${polColor(p)}">${POL_LABEL[p]}</span>`).join("");
      m.bindPopup(`<div class="station-popup">
        <div class="zone">${s.zone}</div>
        <h4>${s.station}</h4>
        <div class="addr">${s.address}</div>
        <div class="pols">${pols}</div>
      </div>`);
      m.bindTooltip(s.station, { direction: "top", offset: [0, -8] });
      MARKERS.push(m);
    });
    // legend
    $("#mapLegend").innerHTML = STATE.data.stations.map(s =>
      `<span class="ml"><span class="pin" style="background:${stationColor(s.station)}"></span>${s.station}</span>`).join("");
  }
  function highlightMapPollutant() {
    // emphasize stations measuring the selected pollutant
    if (!MAP) return;
    const f = STATE.filters;
    STATE.data.stations.forEach((s, i) => {
      const measures = s.pollutants.includes(f.pollutant);
      const focus = f.station === "All" ? measures : s.station === f.station;
      MARKERS[i].setStyle({ fillOpacity: focus ? 1 : 0.25, radius: (f.station !== "All" && s.station === f.station) ? 14 : 11, weight: focus ? 2 : 1 });
    });
  }
  function refreshMapTiles() {
    if (!MAP || !TILE) return;
    TILE.setUrl(TILES[currentTheme()]);
  }

  /* ============================================================
     Hero sparkline (NO₂ ciudad)
     ============================================================ */
  function renderHeroPollutantChips() {
    const chips = $$(".hero-tags .pchip");
    chips.forEach((chip) => {
      chip.setAttribute("aria-pressed", String(chip.dataset.pollutant === STATE.filters.pollutant));
    });
  }
  function bindHeroPollutantChips() {
    const wrapper = $(".hero-tags");
    if (!wrapper) return;
    wrapper.onclick = (event) => {
      const chip = event.target.closest(".pchip[data-pollutant]");
      if (!chip) return;
      STATE.filters.pollutant = chip.dataset.pollutant;
      renderFilters();
      applyFilters();
    };
  }
  function renderHero() {
    const pollutant = STATE.filters.pollutant;
    const rows = STATE.data.yearly_trends.filter(d => d.pollutant === pollutant);
    const years = []; for (let y = STATE.data.summary.period_start; y <= STATE.data.summary.period_end; y++) years.push(y);
    const cityAvg = years.map(y => {
      const yr = rows.filter(d => d.year === y);
      return yr.length ? yr.reduce((a, b) => a + b.avg_value, 0) / yr.length : NaN;
    });
    const validAvg = cityAvg.filter((value) => Number.isFinite(value));
    if (!validAvg.length) return;
    const first = validAvg[0], last = validAvg[validAvg.length - 1];
    const change = first ? ((last - first) / first) * 100 : 0;
    $(".hc-title") && ($(".hc-title").textContent = `${POL_LABEL[pollutant]} · promedio ciudad`);
    $(".hc-sub") && ($(".hc-sub").textContent = `4 estaciones · ${STATE.data.summary.period_start} – ${STATE.data.summary.period_end}`);
    $(".hc-legend span") && ($(".hc-legend span").innerHTML = `<i style="background:${polColor(pollutant)}"></i>Promedio anual de ${POL_LABEL[pollutant]} (${unitOf(pollutant)})`);
    $("#heroBig").innerHTML = `${last.toFixed(1)}<span class="hc-unit"> ${unitOf(pollutant) || ""}</span>`;
    $("#heroTrend").innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" width="14" height="14"><path d="M17 7L7 17M7 17h7M7 17v-7"/></svg> ${change.toFixed(0)}% vs. ${STATE.data.summary.period_start}`;
    const col = polColor(pollutant);
    const lay = {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      margin: { l: 0, r: 0, t: 6, b: 0 }, height: 132,
      xaxis: { visible: false, fixedrange: true }, yaxis: { visible: false, fixedrange: true },
      showlegend: false, hovermode: "x",
      hoverlabel: { bgcolor: cssvar("--surface"), bordercolor: cssvar("--border"), font: { family: "Hanken Grotesk", color: cssvar("--text"), size: 12 } },
    };
    const traces = [
      { x: years, y: cityAvg.map(v => v + 0), fill: "tozeroy", fillcolor: hexA(col, .12), line: { width: 0 }, hoverinfo: "skip", type: "scatter" },
      { x: years, y: cityAvg, mode: "lines", line: { color: col, width: 2.6, shape: "spline" }, type: "scatter",
        hovertemplate: `%{x}<br><b>%{y:.1f} ${unitOf(pollutant) || ""}</b><extra></extra>` },
    ];
    Plotly.react("heroSpark", traces, lay, { responsive: true, displayModeBar: false, staticPlot: false });
  }

  /* ---------- utilidades color ---------- */
  function hexA(hex, a) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
    const r = parseInt(hex.slice(0, 2), 16), g = parseInt(hex.slice(2, 4), 16), b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${a})`;
  }

  /* ============================================================
     Tema
     ============================================================ */
  function currentTheme() { return document.documentElement.getAttribute("data-theme") || "light"; }
  function setTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("aireba-theme", t); } catch (e) {}
    // re-render charts with new palette
    if (STATE.data) {
      renderHero(); renderYearlyChart(); renderMonthlyChart();
      renderAnomaliesChart(); renderAnomaliesTable();
      refreshMapTiles();
      MARKERS.forEach((m, i) => m.setStyle({ fillColor: stationColor(STATE.data.stations[i].station) }));
      highlightMapPollutant();
    }
  }
  function initTheme() {
    let t = "light";
    try { t = localStorage.getItem("aireba-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch (e) {}
    document.documentElement.setAttribute("data-theme", t);
    $("#themeToggle").onclick = () => setTheme(currentTheme() === "dark" ? "light" : "dark");
  }

  /* ============================================================
     Init
     ============================================================ */
  async function init() {
    initTheme();
    const ok = await loadAllData();
    if (!ok) return;
    bindHeroPollutantChips();
    renderSummaryCards();
    renderFilters();
    renderHero();
    renderStationsMap();
    // table sort handlers
    $$("#anomTable thead th.sortable").forEach(th => {
      th.onclick = () => {
        const k = th.dataset.key;
        if (STATE.sort.key === k) STATE.sort.dir = STATE.sort.dir === "asc" ? "desc" : "asc";
        else { STATE.sort.key = k; STATE.sort.dir = (k === "date" || k === "severity") ? "desc" : "desc"; }
        renderAnomaliesTable();
      };
    });
    $$("#topNctrl button").forEach(b => {
      b.onclick = () => {
        STATE.topN = +b.dataset.n;
        $$("#topNctrl button").forEach(x => x.setAttribute("aria-pressed", x === b));
        renderAnomaliesTable();
      };
    });
    applyFilters();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
