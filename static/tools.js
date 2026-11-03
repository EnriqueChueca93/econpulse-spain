// Macroscope Spain: interactive tools. The data comes from data/tools.js (written by the
// build); every number here is recomputed in the browser when a control changes, and the
// charts are drawn by app.js (window.EP.render) so they follow the light/dark theme.
(function () {
  "use strict";

  var D = (window.EP && window.EP.tools) || {};
  var render = window.EP && window.EP.render;
  if (!render) return;

  // The page's language (the Spanish site is under es/) and its words for what this script writes. Sentences with
  // figures are written per language below; the series names come from data/tools.js in the page's language.
  var LANG = document.documentElement.lang === "es" ? "es" : "en";
  var ES = {
    "Actual": "Datos observados", "Pre-COVID trend": "Tendencia previa a la COVID", "Series": "Serie", "Gap": "Desviación",
    "ECB deposit rate": "Tipo de depósito del BCE", "Rule, euro area": "Regla, zona del euro", "Rule, Spain": "Regla, España",
    "euro area": "zona del euro", "Spain": "España", "Germany": "Alemania", "AAA euro area": "Zona del euro AAA",
    "Spain 10-year yield": "Rentabilidad a 10 años de España", "German 10-year yield": "Rentabilidad a 10 años de Alemania",
    "Prima de riesgo (over Germany)": "Prima de riesgo (frente a Alemania)",
    "AAA 1-year rate (near-term policy) × 0.1": "Tipo AAA a 1 año (política monetaria a corto plazo) × 0.1",
    "AAA 1-to-10-year forward × 0.9": "Tipo a plazo AAA de 1 a 10 años × 0.9", "Spread over AAA": "Diferencial sobre AAA",
    "The same move, against the AAA curve": "El mismo movimiento, frente a la curva AAA",
    "AAA 1-year × 0.1": "AAA a 1 año × 0.1", "AAA forward × 0.9": "AAA a plazo × 0.9", "Total": "Total",
    "Part": "Componente", "Change": "Variación", "bp": "pb",
    "Not enough data before COVID for that start year.": "No hay datos suficientes antes de la COVID para ese año de inicio.",
    "Pick an end date after the start date.": "Elija una fecha final posterior a la inicial."
  };
  function t(s) { return LANG === "es" && ES[s] !== undefined ? ES[s] : s; }
  var MONTHS = LANG === "es" ? ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                             : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var BP = " " + t("bp");

  function $(id) { return document.getElementById(id); }
  function signed(v, decimals, unit) {
    var s = Math.abs(v).toFixed(decimals);
    if (parseFloat(s) === 0) return s + unit;
    return (v > 0 ? "+" : "−") + s + unit;
  }
  function year(iso) { return parseInt(iso.slice(0, 4), 10) + (parseInt(iso.slice(5, 7), 10) - 1) / 12; }
  function setText(id, text) { var el = $(id); if (el) el.textContent = text; }

  // ---------------------------------------------------------------- 1. Economy vs pre-COVID trend
  // A log-linear trend fitted from January of the chosen year to the last reading before COVID
  // (December 2019, or the fourth quarter), extended to today.
  function fitTrend(s, startYear) {
    var end = s.freq === "Q" ? "2019-10-01" : "2019-12-01";
    var start = startYear + "-01-01";
    var n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (var i = 0; i < s.x.length; i++) {
      if (s.x[i] >= start && s.x[i] <= end && s.y[i] > 0) {
        var t = year(s.x[i]), y = Math.log(s.y[i]);
        n++; sx += t; sy += y; sxx += t * t; sxy += t * y;
      }
    }
    if (n < 8) return null;
    var b = (n * sxy - sx * sy) / (n * sxx - sx * sx), a = (sy - b * sx) / n;
    var trend = s.x.map(function (d) { return Math.exp(a + b * year(d)); });
    var last = s.y.length - 1;
    var base = trend[s.x.indexOf(end)] || trend[last];
    return { trend: trend, base: base, growth: Math.exp(b) - 1, gap: s.y[last] / trend[last] - 1, end: end };
  }

  function dayLabel(iso) {
    return parseInt(iso.slice(8, 10), 10) + " " + MONTHS[parseInt(iso.slice(5, 7), 10) - 1] + " " + iso.slice(0, 4);
  }

  function dateLabel(iso, freq) {
    var m = parseInt(iso.slice(5, 7), 10);
    return freq === "Q" ? (LANG === "es" ? "T" : "Q") + (Math.floor((m - 1) / 3) + 1) + " " + iso.slice(0, 4)
                        : MONTHS[m - 1] + " " + iso.slice(0, 4);
  }

  function initTrend() {
    var series = D.trend || [];
    var pick = $("trend-series"), from = $("trend-start");
    if (!pick || !series.length) return;
    series.forEach(function (s, i) {
      var o = document.createElement("option"); o.value = i; o.textContent = s.label; pick.appendChild(o);
    });

    function update() {
      var s = series[pick.value], startYear = parseInt(from.value, 10);
      var fit = fitTrend(s, startYear);
      if (!fit) { setText("trend-result", t("Not enough data before COVID for that start year.")); return; }
      var keep = function (d) { return d >= startYear + "-01-01"; };
      var x = s.x.filter(keep), idx = s.x.map(function (d, i) { return keep(d) ? i : -1; }).filter(function (i) { return i >= 0; });
      render({
        id: "trend-line", kind: "line", unit: "", decimals: 1, freq: s.freq,
        series: [
          { name: t("Actual"), x: x, y: idx.map(function (i) { return +(100 * s.y[i] / fit.base).toFixed(2); }) },
          { name: t("Pre-COVID trend"), x: x, y: idx.map(function (i) { return +(100 * fit.trend[i] / fit.base).toFixed(2); }),
            color: "ink", dash: "dot" }
        ]
      });
      // The gap for every series, with the same trend window.
      var gaps = series.map(function (t) { var f = fitTrend(t, startYear); return f ? { label: t.label, gap: f.gap } : null; })
        .filter(Boolean).sort(function (a, b) { return b.gap - a.gap; });
      render({
        id: "trend-gaps", kind: "hbar", unit: "%", decimals: 1, x_title: t("Series"), highlight: s.label,
        series: [{ name: t("Gap"), x: gaps.map(function (g) { return g.label; }), y: gaps.map(function (g) { return +(100 * g.gap).toFixed(2); }) }],
        ref_lines: []
      });
      var last = s.x.length - 1, gap = Math.abs(100 * fit.gap).toFixed(1), growth = (100 * fit.growth).toFixed(1);
      setText("trend-result", LANG === "es"
        ? s.label + ", " + dateLabel(s.x[last], s.freq) + ": un " + gap + "%" + (fit.gap >= 0 ? " por encima" : " por debajo") +
          " de la tendencia que seguía de " + startYear + " a 2019 (crecimiento del " + growth + "% anual)."
        : s.label + " in " + dateLabel(s.x[last], s.freq) + " is " + gap + "%" + (fit.gap >= 0 ? " above" : " below") +
          " the trend it was on from " + startYear + " to 2019 (growth of " + growth + "% a year).");
    }
    pick.addEventListener("change", update);
    from.addEventListener("change", update);
    update();
  }

  // ---------------------------------------------------------------- 2. Taylor rule
  // rate = r* + inflation + a × (inflation − 2%) − b × (unemployment − its trend)
  function initTaylor() {
    var T = D.taylor;
    if (!T || !$("taylor-rstar")) return;
    var controls = ["taylor-region", "taylor-measure", "taylor-rstar", "taylor-a", "taylor-b"].map($);

    function rule(r, measure, rstar, a, b) {
      var x = [], y = [];
      for (var i = 0; i < r.x.length; i++) {
        var p = measure === "core" ? r.core[i] : r.inflation[i];
        if (p === null || p === undefined) continue;
        x.push(r.x[i]);
        y.push(+(rstar + p + a * (p - T.target) - b * (r.unemployment[i] - r.trend[i])).toFixed(3));
      }
      return { x: x, y: y };
    }

    function update() {
      var region = controls[0].value, measure = controls[1].value;
      var rstar = parseFloat(controls[2].value), a = parseFloat(controls[3].value), b = parseFloat(controls[4].value);
      setText("taylor-rstar-out", rstar.toFixed(2) + "%");
      setText("taylor-a-out", a.toFixed(1));
      setText("taylor-b-out", b.toFixed(1));
      var series = [];
      if (T.dfr) series.push({ name: t("ECB deposit rate"), x: T.dfr.x, y: T.dfr.y, shape: "hv" });
      var latest = [];
      [["ea", "Rule, euro area", "euro area"], ["es", "Rule, Spain", "Spain"]].forEach(function (pair) {
        if (region !== "both" && region !== pair[0]) return;
        var r = rule(T[pair[0]], measure, rstar, a, b);
        if (!r.x.length) return;
        series.push({ name: t(pair[1]), x: r.x, y: r.y });
        latest.push(t(pair[2]) + " " + r.y[r.y.length - 1].toFixed(1) + "% (" + dateLabel(r.x[r.x.length - 1], "M") + ")");
      });
      render({ id: "taylor-tool", kind: "line", unit: "%", decimals: 1, freq: "M", series: series, ref_lines: [] });
      var dfr = T.dfr ? T.dfr.y[T.dfr.y.length - 1] : null;
      setText("taylor-result", LANG === "es"
        ? "La regla sugiere: " + latest.join("; ") + "." + (dfr !== null ? " El tipo de depósito del BCE es del " + dfr.toFixed(2) + "%." : "")
        : "The rule suggests: " + latest.join("; ") + "." + (dfr !== null ? " The ECB's deposit rate is " + dfr.toFixed(2) + "%." : ""));
    }
    controls.forEach(function (c) { c.addEventListener("input", update); c.addEventListener("change", update); });
    $("taylor-reset").addEventListener("click", function () {
      controls[2].value = T.r_star; controls[3].value = 0.5; controls[4].value = 1.0; update();
    });
    update();
  }

  // ---------------------------------------------------------------- 3. Interest rate decomposer
  // Spain 10y = German 10y + prima de riesgo, and = AAA 10y + spread over AAA, where the AAA
  // 10-year is one tenth today's 1-year rate plus nine tenths the 1-to-10-year forward rate.
  function initRates() {
    var R = D.rates;
    if (!R || !$("rates-start")) return;
    var start = $("rates-start"), end = $("rates-end");
    var first = R.x[0], last = R.x[R.x.length - 1];
    [start, end].forEach(function (el) { el.min = first; el.max = last; });
    end.value = last;
    start.value = last.slice(0, 4) - 1 + "-12-31";

    function at(date) {  // the last day with data on or before `date`
      var lo = 0, hi = R.x.length - 1;
      if (date < R.x[0]) return 0;
      while (lo < hi) { var mid = Math.ceil((lo + hi) / 2); if (R.x[mid] <= date) lo = mid; else hi = mid - 1; }
      return lo;
    }
    function fwd(i) { return (10 * R.aaa10[i] - R.aaa1[i]) / 9; }

    function update() {
      var i = at(start.value || first), j = at(end.value || last);
      if (j <= i) { setText("rates-result", t("Pick an end date after the start date.")); return; }
      var bp = function (v) { return 100 * v; };
      var total = bp(R.es10[j] - R.es10[i]);
      var parts = [
        [t("German 10-year yield"), bp(R.de10[j] - R.de10[i])],
        [t("Prima de riesgo (over Germany)"), bp((R.es10[j] - R.de10[j]) - (R.es10[i] - R.de10[i]))],
        [t("AAA 1-year rate (near-term policy) × 0.1"), 0.1 * bp(R.aaa1[j] - R.aaa1[i])],
        [t("AAA 1-to-10-year forward × 0.9"), 0.9 * bp(fwd(j) - fwd(i))],
        [t("Spread over AAA"), bp((R.es10[j] - R.aaa10[j]) - (R.es10[i] - R.aaa10[i]))]
      ];
      var rows = [[t("Spain 10-year yield"), total, 0]].concat(parts.map(function (p, k) { return [p[0], p[1], k < 2 ? 1 : 2]; }));
      var body = $("rates-table").querySelector("tbody");
      body.textContent = "";
      rows.forEach(function (r, k) {
        if (k === 3) {
          var g = body.insertRow(); g.className = "group-row";
          var c = g.insertCell(); c.colSpan = 2; c.textContent = t("The same move, against the AAA curve");
        }
        var tr = body.insertRow(), th = document.createElement("th");
        th.scope = "row"; th.className = "indent-" + (r[2] ? 1 : 0); th.textContent = r[0]; tr.appendChild(th);
        var td = tr.insertCell(); td.className = "num"; td.textContent = signed(r[1], 0, BP);
      });
      setText("rates-result", LANG === "es"
        ? "Del " + dayLabel(R.x[i]) + " al " + dayLabel(R.x[j]) + ", la rentabilidad a 10 años de España varió " + signed(total, 0, BP) +
          ": " + signed(parts[0][1], 0, BP) + " por la rentabilidad alemana y " + signed(parts[1][1], 0, BP) + " por la prima de riesgo."
        : "From " + dayLabel(R.x[i]) + " to " + dayLabel(R.x[j]) + ", Spain's 10-year yield moved " + signed(total, 0, BP) +
          ": " + signed(parts[0][1], 0, BP) + " from the German yield and " + signed(parts[1][1], 0, BP) + " from the prima de riesgo.");
      render({
        id: "rates-parts", kind: "bar", signed: true, unit: t("bp"), decimals: 0, x_kind: "category", x_title: t("Part"),
        series: [{ name: t("Change"), x: ["AAA 1-year × 0.1", "AAA forward × 0.9", "Spread over AAA", "Total"].map(t),
          y: [parts[2][1], parts[3][1], parts[4][1], total].map(function (v) { return +v.toFixed(1); }) }],
        ref_lines: []
      });
      var xs = R.x.slice(i, j + 1);
      render({
        id: "rates-levels", kind: "line", unit: "%", decimals: 2, freq: "D", date_format: "%-d %b %Y",
        series: [{ name: t("Spain"), x: xs, y: R.es10.slice(i, j + 1) }, { name: t("Germany"), x: xs, y: R.de10.slice(i, j + 1) },
          { name: t("AAA euro area"), x: xs, y: R.aaa10.slice(i, j + 1) }],
        ref_lines: []
      });
    }
    [start, end].forEach(function (el) { el.addEventListener("change", update); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-rates-preset]"), function (btn) {
      btn.addEventListener("click", function () {
        var y = parseInt(last.slice(0, 4), 10), p = btn.getAttribute("data-rates-preset");
        end.value = last;
        start.value = p === "ytd" ? (y - 1) + "-12-31" : p === "year" ? (y - 1) + last.slice(4) : p;
        update();
      });
    });
    update();
  }

  initTrend();
  initTaylor();
  initRates();
})();
