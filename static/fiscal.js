// Macroscope Spain: the Fiscal Explorer (site/fiscal-explorer.html), after Econvitals' Fiscal Explorer.
// The baseline comes from data/fiscal.js (econpulse/fiscal.py): the European Commission's debt
// projection to 2036, extended to 2070 on its long-term assumptions. Levers change the path from
// 2027 through the same debt equation, written as changes from the baseline, so with every lever
// at zero the page shows the baseline exactly:
//   d(t) = d(t-1) (1 + i) / (1 + g) - pb(t) + sfa(t)
(function () {
  "use strict";

  var F = window.EP && window.EP.fiscal;
  var render = window.EP && window.EP.render;
  if (!F || !render) return;

  var B = F.baseline, Y = F.years;
  var DEFAULTS = { view: "future", series: "balance", horizon: 2056, adj: 0, ageing: 100, growth: 0, inflation: 0,
                   rate: 0, compare: false, past: ["debt_annual", "revenue_annual", "spending_annual"] };
  var state = Object.assign({}, DEFAULTS);
  var SERIES = {
    debt: { label: "Gross public debt", unit: "% of GDP" },
    balance: { label: "Overall balance", unit: "% of GDP" },
    pb: { label: "Primary balance", unit: "% of GDP" },
    interest: { label: "Interest", unit: "% of GDP" },
    rg: { label: "Interest rate and growth", unit: "%" },
    ageing: { label: "Ageing costs", unit: "% of GDP" }
  };

  function $(id) { return document.getElementById(id); }
  function idx(year) { return Y.indexOf(year); }
  function iso(year) { return year + "-01-01"; }
  function fmt(v, d) { return (v < 0 ? "−" : "") + Math.abs(v).toFixed(d === undefined ? 1 : d); }
  function signed(v, d) { return (v > 0 ? "+" : "") + fmt(v, d); }

  // ---------------------------------------------------------------- the model
  function project(p) {
    var out = { debt: [], pb: [], interest: [], balance: [], i: [], g: [] };
    var dd = 0;   // scenario debt minus baseline debt
    for (var k = 0; k < Y.length; k++) {
      var y = Y[k];
      if (y < F.first_lever_year || k === 0) {
        out.debt.push(B.debt[k]); out.pb.push(B.pb[k]); out.interest.push(B.interest[k]);
        out.balance.push(B.balance[k]); out.i.push(B.i[k]); out.g.push(B.g[k]);
        continue;
      }
      var years = y - F.first_lever_year + 1;
      var gB = B.g[k] / 100, iB = B.i[k] / 100;
      var gS = (1 + (B.real[k] + p.growth) / 100) * (1 + (B.inflation[k] + p.inflation) / 100) - 1;
      // New market rates (and inflation, which lenders demand back) reach the debt as it is refinanced.
      var iS = iB + (p.rate + p.inflation) / 100 * Math.min(1, years / F.maturity);
      var dpb = p.adj + (1 - p.ageing / 100) * B.coa[k];
      var prevB = B.debt[k - 1], prevS = out.debt[k - 1];
      dd = dd * (1 + iS) / (1 + gS) + prevB * ((1 + iS) / (1 + gS) - (1 + iB) / (1 + gB)) - dpb;
      var interest = iS * prevS / (1 + gS);   // debt is in % of GDP, so this is too
      out.debt.push(B.debt[k] + dd);
      out.pb.push(B.pb[k] + dpb);
      out.interest.push(interest);
      out.balance.push(B.pb[k] + dpb - interest);
      out.i.push(100 * iS); out.g.push(100 * gS);
    }
    return out;
  }

  function levers(p) { return { adj: p.adj, ageing: p.ageing, growth: p.growth, inflation: p.inflation, rate: p.rate }; }
  function baselineLevers() { return { adj: 0, ageing: 100, growth: 0, inflation: 0, rate: 0 }; }

  // Goals: the permanent change in the primary balance from 2027 that meets each, found by bisection.
  var GOALS = {
    hold: { label: "Hold debt at its 2025 level", test: function (r, end) { return r.debt[idx(end)] <= B.debt[idx(2025)]; } },
    sixty: { label: "Bring debt down to 60% of GDP", test: function (r, end) { return r.debt[idx(end)] <= 60; } },
    deficit3: { label: "Keep the deficit at or below 3% every year", test: function (r, end) {
      for (var y = F.first_lever_year; y <= end; y++) { if (r.balance[idx(y)] < -3 - 1e-9) return false; }
      return true;
    } }
  };
  function solve(goal, p, end) {
    var lo = -15, hi = 25, q = Object.assign({}, p);
    for (var n = 0; n < 60; n++) {
      var mid = (lo + hi) / 2; q.adj = mid;
      if (GOALS[goal].test(project(q), end)) hi = mid; else lo = mid;
    }
    return hi;
  }

  // ---------------------------------------------------------------- charts
  function historyFor(id) {
    var h = F.history[id];
    return h ? { x: h.years.map(iso), y: h.values } : null;
  }

  function futureSeries(key, run, end, label) {
    var x = [], y = [];
    for (var k = 0; k < Y.length && Y[k] <= end; k++) {
      if (Y[k] < 2025) continue;
      var v;
      if (key === "ageing") v = B.pensions[k] + B.health[k] + B.ltc[k] + B.education[k];
      else v = run[key][k];
      if (v === null || v === undefined) continue;
      x.push(iso(Y[k])); y.push(+v.toFixed(2));
    }
    return { name: label, x: x, y: y };
  }

  function drawFuture(run, base, end) {
    var changed = JSON.stringify(levers(state)) !== JSON.stringify(baselineLevers());
    var debtHist = historyFor("debt_annual");
    var series = [{ name: "Actual", x: debtHist.x.filter(function (d) { return d >= "2000"; }),
                    y: debtHist.y.slice(debtHist.x.findIndex(function (d) { return d >= "2000"; })), color: "ink" },
                  Object.assign(futureSeries("debt", base, end, "Baseline"), { dash: "dash" })];
    if (changed) series.push(futureSeries("debt", run, end, "Your scenario"));
    if (state.compare) {
      var worst = F.scenarios["Adverse interest-growth differential"];
      if (worst) series.push({ name: "Commission: adverse r − g", x: Object.keys(worst).filter(function (y) { return +y >= 2025; }).map(iso),
                               y: Object.keys(worst).filter(function (y) { return +y >= 2025; }).map(function (y) { return worst[y]; }), dash: "dot" });
    }
    render({ id: "fx-debt", kind: "line", unit: "%", decimals: 1, freq: "A", series: series,
             ref_lines: [{ y: 60, label: "60% (EU reference)" }] });

    var key = state.series, meta = SERIES[key], second = [];
    var histIds = { balance: "deficit_annual", pb: "primary_balance", interest: "interest_annual" };
    if (key === "rg") {
      second = [futureSeries("i", run, end, "Interest rate on the debt"), futureSeries("g", run, end, "Nominal GDP growth")];
    } else if (key === "ageing") {
      second = ["pensions", "health", "ltc", "education"].slice(0, 3).map(function (k) {
        var x = [], y = [];
        for (var j = 0; j < Y.length && Y[j] <= end; j++) { if (B[k][j] !== null) { x.push(iso(Y[j])); y.push(+B[k][j].toFixed(2)); } }
        return { name: { pensions: "Pensions", health: "Health care", ltc: "Long-term care" }[k], x: x, y: y };
      });
      second.push(Object.assign(futureSeries("ageing", run, end, "Total, with education"), { color: "ink" }));
    } else {
      var h = historyFor(histIds[key]);
      if (h) second.push({ name: "Actual", x: h.x.filter(function (d) { return d >= "2000"; }),
                           y: h.y.slice(h.x.findIndex(function (d) { return d >= "2000"; })), color: "ink" });
      second.push(Object.assign(futureSeries(key, base, end, "Baseline"), { dash: "dash" }));
      if (changed) second.push(futureSeries(key, run, end, "Your scenario"));
    }
    $("fx-second-title").textContent = meta.label;
    $("fx-second-subtitle").textContent = key === "rg" ? "%, a year" : key === "ageing"
      ? "% of GDP, the Commission's 2024 Ageing Report (pensions, health care, long-term care, education)" : "% of GDP";
    render({ id: "fx-second", kind: "line", unit: "%", decimals: 1, freq: "A", series: second,
             ref_lines: key === "balance" ? [{ y: -3, label: "−3% (EU limit)" }] : [] });
  }

  function drawPast() {
    var picks = state.past.filter(function (id) { return F.history[id]; }).slice(0, 3);
    var series = picks.map(function (id) { var h = historyFor(id); return { name: F.history[id].label, x: h.x, y: h.y }; });
    render({ id: "fx-past", kind: "line", unit: "%", decimals: 1, freq: "A", series: series, ref_lines: [] });
  }

  // ---------------------------------------------------------------- readout
  function readout(run, base, end) {
    var p = levers(state), b = baselineLevers();
    var rows = [
      ["Debt in 2036", fmt(base.debt[idx(2036)]) + "%", fmt(run.debt[idx(2036)]) + "%"],
      ["Debt in " + end, fmt(base.debt[idx(end)]) + "%", fmt(run.debt[idx(end)]) + "%"],
      ["Overall balance in " + end, fmt(base.balance[idx(end)]) + "%", fmt(run.balance[idx(end)]) + "%"],
      ["Interest in " + end, fmt(base.interest[idx(end)]) + "%", fmt(run.interest[idx(end)]) + "%"]
    ];
    Object.keys(GOALS).forEach(function (g) {
      rows.push(["Adjustment to " + GOALS[g].label.charAt(0).toLowerCase() + GOALS[g].label.slice(1) + " by " + end,
                 signed(solve(g, b, end), 2) + " pp", signed(solve(g, p, end), 2) + " pp"]);
    });
    var body = $("fx-readout").querySelector("tbody");
    body.textContent = "";
    rows.forEach(function (r) {
      var tr = body.insertRow(), th = document.createElement("th");
      th.scope = "row"; th.textContent = r[0]; tr.appendChild(th);
      [r[1], r[2]].forEach(function (v) { var td = tr.insertCell(); td.className = "num"; td.textContent = v; });
    });
    var gap = solve("hold", p, end), onBaseline = JSON.stringify(p) === JSON.stringify(b);
    var hold = "holding it at its 2025 level (" + fmt(B.debt[idx(2025)]) + "%) would take a primary balance " + fmt(gap, 2) +
      "% of GDP above the baseline every year from " + F.first_lever_year;
    $("fx-result").textContent = (onBaseline ? "On the baseline" : "In your scenario") + ", debt reaches " +
      fmt(run.debt[idx(end)]) + "% of GDP in " + end + "; " + hold +
      (onBaseline || Math.abs(gap - p.adj) < 0.005 ? "." : " (your budget lever is at " + signed(p.adj, 2) + ").");
  }

  // ---------------------------------------------------------------- controls and state
  var SLIDERS = [["fx-adj", "adj", 1], ["fx-ageing", "ageing", 0], ["fx-growth", "growth", 1], ["fx-inflation", "inflation", 1],
                 ["fx-rate", "rate", 1]];

  function readHash() {
    if (location.hash.length < 2 || location.hash.indexOf("#fig-") === 0) return;
    try {
      var s = JSON.parse(atob(location.hash.slice(1)));
      Object.keys(DEFAULTS).forEach(function (k) { if (s[k] !== undefined) state[k] = s[k]; });
    } catch (e) { /* not a scenario link */ }
  }
  function shareLink() {
    return location.href.split(/[?#]/)[0] + "#" + btoa(JSON.stringify(state));
  }

  function syncControls() {
    SLIDERS.forEach(function (s) {
      var el = $(s[0]); el.value = state[s[1]];
      $(s[0] + "-out").textContent = s[1] === "ageing" ? state.ageing + "%"
        : signed(+state[s[1]], s[1] === "adj" && Math.round(state.adj * 10) !== state.adj * 10 ? 2 : s[2]) + " pp";
    });
    $("fx-series").value = state.series;
    $("fx-compare").checked = state.compare;
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-view]"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-fx-view") === state.view ? "true" : "false");
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-horizon]"), function (b) {
      b.setAttribute("aria-pressed", +b.getAttribute("data-fx-horizon") === state.horizon ? "true" : "false");
    });
    $("fx-future").hidden = state.view !== "future";
    $("fx-past-panel").hidden = state.view !== "past";
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-past]"), function (c) {
      c.checked = state.past.indexOf(c.value) >= 0;
    });
  }

  function update() {
    syncControls();
    if (state.view === "past") { drawPast(); return; }
    var end = state.horizon;
    var run = project(levers(state)), base = project(baselineLevers());
    drawFuture(run, base, end);
    readout(run, base, end);
  }

  function init() {
    readHash();
    SLIDERS.forEach(function (s) {
      $(s[0]).addEventListener("input", function () { state[s[1]] = +this.value; update(); });
    });
    $("fx-series").addEventListener("change", function () { state.series = this.value; update(); });
    $("fx-compare").addEventListener("change", function () { state.compare = this.checked; update(); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-view]"), function (b) {
      b.addEventListener("click", function () { state.view = b.getAttribute("data-fx-view"); update(); });
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-horizon]"), function (b) {
      b.addEventListener("click", function () { state.horizon = +b.getAttribute("data-fx-horizon"); update(); });
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-goal]"), function (b) {
      b.addEventListener("click", function () {
        // The exact answer (to 0.01): the slider shows the nearest step, the label the value used.
        state.adj = Math.round(solve(b.getAttribute("data-fx-goal"), levers(state), state.horizon) * 100) / 100;
        update();
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-fx-past]"), function (c) {
      c.addEventListener("change", function () {
        var on = Array.prototype.filter.call(document.querySelectorAll("[data-fx-past]"), function (x) { return x.checked; })
          .map(function (x) { return x.value; });
        if (on.length > 3) { c.checked = false; return; }   // three lines at most, for legibility
        state.past = on; update();
      });
    });
    $("fx-reset").addEventListener("click", function () {
      ["adj", "ageing", "growth", "inflation", "rate"].forEach(function (k) { state[k] = DEFAULTS[k]; });
      update();
    });
    $("fx-share").addEventListener("click", function () {
      var url = shareLink(), btn = this, label = btn.textContent;
      var done = function () { btn.textContent = "Link copied"; setTimeout(function () { btn.textContent = label; }, 2000); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link:", url); });
      else window.prompt("Copy this link:", url);
    });
    update();
  }

  init();
  window.EP.fiscalModel = { project: project, solve: solve };   // for checking in the browser console
})();
