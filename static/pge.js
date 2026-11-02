// EconPulse Spain: the Budget explorer's section on the State's budget (Batch 30c). What the Presupuestos
// Generales del Estado plan by spending policy and revenue chapter (the consolidated budget, by year in force),
// and how much of its own budget the State has spent, and how fast, from data/budget.js (econpulse/budget.py).
// Charts are drawn by the site's own renderer (EP.render).
(function () {
  "use strict";

  var S = window.EP && window.EP.budget && window.EP.budget.state_budget;
  var render = window.EP && window.EP.render;
  if (!S || !render || !document.getElementById("bx-pge")) return;

  var Y = S.years;
  var state = { kind: "spending", measure: "eur", year: Y[Y.length - 1], base: Y[0], selected: [],
                exYear: S.execution.length ? S.execution[0].year : null };

  function $(id) { return document.getElementById(id); }
  function iso(y) { return y + "-01-01"; }
  function rolled(y) { return S.rolled_over.indexOf(y) >= 0; }
  function yearLabel(y) { return y + (rolled(y) ? " (rolled over)" : ""); }
  function find(list, code) { for (var i = 0; i < list.length; i++) { if (list[i].code === code) return list[i]; } return null; }
  function at(series, y) { var k = Y.indexOf(y); return k < 0 || !series ? null : series[k]; }
  function measure() {
    return state.measure === "gdp" ? { label: "% of GDP", unit: "%", decimals: 2, suffix: "%", prefix: "" }
                                   : { label: "€ bn", unit: "", decimals: 1, suffix: " bn", prefix: "€" };
  }
  function convert(series) {
    return series.map(function (v, k) {
      if (v === null || v === undefined) return null;
      return state.measure === "gdp" ? (S.gdp[k] ? v / S.gdp[k] * 100 : null) : v / 1000;
    });
  }
  function fmt(v, m) {
    if (v === null || v === undefined || isNaN(v)) return "–";
    var s = Math.abs(v).toLocaleString("en-GB", { minimumFractionDigits: m.decimals, maximumFractionDigits: m.decimals });
    return (v < 0 ? "−" : "") + m.prefix + s + m.suffix;
  }
  function bn(v) { return v === null || v === undefined ? "–" : (v / 1000).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 }); }
  function change(now, then) {
    if (now === null || then === null || now === undefined || then === undefined) return "–";
    if (state.measure === "gdp") { var d = now - then; return (d > 0 ? "+" : d < 0 ? "−" : "") + Math.abs(d).toFixed(2) + " pp"; }
    if (!then) return "–";
    var c = (now / then - 1) * 100;
    return (c > 0 ? "+" : c < 0 ? "−" : "") + Math.abs(c).toFixed(1) + "%";
  }
  function short(label) { return label.length > 44 ? label.slice(0, 42) + "…" : label; }

  // ---------------------------------------------------------------- what the budget plans
  function draw() {
    var m = measure();
    var list = state.kind === "spending" ? S.policies : S.revenues;
    var table = state.kind === "spending" ? S.spending : S.revenue;
    var ys = Y.filter(function (y) { return at(table.TOTAL, y) !== null && (state.measure !== "gdp" || at(S.gdp, y)); });
    if (ys.indexOf(state.year) < 0) state.year = ys[ys.length - 1];
    if (ys.indexOf(state.base) < 0) state.base = ys[0];
    fillYears(ys);
    var rows = list.map(function (it) {
      var conv = convert(table[it.code]);
      return { it: it, conv: conv, now: at(conv, state.year), then: at(conv, state.base),
               share: (at(table[it.code], state.year) || 0) / (at(table.TOTAL, state.year) || NaN) * 100 };
    }).filter(function (r) { return r.now !== null && r.now !== undefined; })
      .sort(function (a, b) { return b.now - a.now; });
    state.selected = state.selected.filter(function (c) { return find(list, c); });
    if (!state.selected.length) state.selected = rows.slice(0, 3).map(function (r) { return r.it.code; });
    var noun = state.kind === "spending" ? "Spending by policy" : "Revenue by chapter";
    var tot = convert(table.TOTAL);

    var raw = at(table.TOTAL, state.year), k = Y.indexOf(state.year);
    var facts = [[(state.kind === "spending" ? "Budgeted spending, " : "Budgeted revenue, ") + state.year,
                  "€" + (raw / 1000).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " bn",
                  (S.gdp[k] ? (raw / S.gdp[k] * 100).toFixed(1) + "% of GDP" : "GDP not yet published") + (rolled(state.year) ? "; a rolled-over budget" : "")]];
    if (state.kind === "spending" && rows.length) {
      facts.push(["The largest policy", short(rows[0].it.label), rows[0].share.toFixed(1) + "% of the total"]);
    }
    $("pge-facts").innerHTML = facts.map(function (f) {
      return '<div class="fact"><span class="fact-label">' + f[0] + '</span><span class="fact-value">' + f[1] + '</span><span class="fact-sub">' + f[2] + "</span></div>";
    }).join("");

    $("pge-mix-title").textContent = noun + ", " + yearLabel(state.year);
    $("pge-mix-subtitle").textContent = "Consolidated budget, initial appropriations · " + m.label;
    var first = find(list, state.selected[0]);
    render({ id: "pge-mix", kind: "hbar", unit: m.unit, decimals: m.decimals, x_title: "", freq: "A",
             highlight: first ? short(first.label) : null,
             series: [{ name: noun, x: rows.map(function (r) { return short(r.it.label); }), y: rows.map(function (r) { return +r.now.toFixed(4); }) }] });

    var series = [{ name: "Total", x: ys.map(iso), y: ys.map(function (y) { return at(tot, y); }), color: "ink" }];
    state.selected.forEach(function (code, i) {
      var r = rows.filter(function (x) { return x.it.code === code; })[0];
      if (r) series.push({ name: short(r.it.label), x: ys.map(iso), y: ys.map(function (y) { return at(r.conv, y); }), slot: i + 1 });
    });
    var rolledShown = S.rolled_over.filter(function (y) { return ys.indexOf(y) >= 0; });
    $("pge-trend-title").textContent = noun + " over time";
    $("pge-trend-subtitle").textContent = m.label + (rolledShown.length ? " · rolled over in " + rolledShown.join(", ") : "");
    render({ id: "pge-trend", kind: "line", unit: m.unit === "%" ? "%" : "", decimals: m.decimals, freq: "A", series: series });

    $("pge-table-caption").textContent = noun + " · consolidated budget · " + m.label;
    $("pge-col-item").textContent = state.kind === "spending" ? "Policy" : "Chapter";
    $("pge-col-year").textContent = yearLabel(state.year);
    $("pge-col-base").textContent = yearLabel(state.base);
    var html = rows.map(function (r) {
      var on = state.selected.indexOf(r.it.code) >= 0;
      return '<tr class="bx-row' + (on ? " highlight-row" : "") + '" data-code="' + r.it.code + '" tabindex="0" aria-selected="' + on + '">' +
             '<th scope="row">' + r.it.label + '</th><td class="num">' + fmt(r.now, m) + '</td><td class="num">' +
             (isNaN(r.share) ? "–" : r.share.toFixed(1) + "%") + '</td><td class="num">' + fmt(r.then, m) + '</td><td class="num">' +
             change(r.now, r.then) + "</td></tr>";
    }).join("");
    html += '<tr class="bx-total"><th scope="row">Total</th><td class="num">' + fmt(at(tot, state.year), m) + '</td><td class="num">100%</td><td class="num">' +
            fmt(at(tot, state.base), m) + '</td><td class="num">' + change(at(tot, state.year), at(tot, state.base)) + "</td></tr>";
    $("pge-table").querySelector("tbody").innerHTML = html;
    drawExecution();
  }

  function fillYears(ys) {
    [["pge-year", state.year], ["pge-base", state.base]].forEach(function (pair) {
      var sel = $(pair[0]);
      var want = ys.slice().reverse().map(function (y) { return '<option value="' + y + '"' + (y === pair[1] ? " selected" : "") + ">" + yearLabel(y) + "</option>"; }).join("");
      if (sel.innerHTML !== want) sel.innerHTML = want;
      sel.value = String(pair[1]);
    });
  }

  // ---------------------------------------------------------------- budgeted and spent
  function drawExecution() {
    if (!S.execution.length || !$("pge-ex-year")) return;
    var sel = $("pge-ex-year");
    var want = S.execution.map(function (e) {
      return '<option value="' + e.year + '"' + (e.year === state.exYear ? " selected" : "") + ">" + (e.full_year ? e.year + ", full year" : e.year + ", to " + e.through) + "</option>";
    }).join("");
    if (sel.innerHTML !== want) sel.innerHTML = want;
    var ex = S.execution.filter(function (e) { return e.year === state.exYear; })[0] || S.execution[0];
    var t = ex.total;
    var when = ex.full_year ? ex.year + ", full year" : "to " + ex.through;
    $("pge-ex-facts").innerHTML = [
      ["Initial budget, " + ex.year, "€" + bn(t.initial) + " bn", "the State's own budget, all chapters"],
      ["After the year's changes", "€" + bn(t.final) + " bn", (t.final >= t.initial ? "+" : "−") + Math.abs((t.final / t.initial - 1) * 100).toFixed(1) + "% on the initial budget"],
      ["Spent", "€" + bn(t.obligations) + " bn", Math.round(t.obligations / t.final * 100) + "% of the final budget, " + when]
    ].map(function (f) {
      return '<div class="fact"><span class="fact-label">' + f[0] + '</span><span class="fact-value">' + f[1] + '</span><span class="fact-sub">' + f[2] + "</span></div>";
    }).join("");
    var rows = ex.rows.filter(function (r) { return r.final > 0; }).map(function (r) {
      return { r: r, pct: r.obligations / r.final * 100 };
    }).sort(function (a, b) { return b.r.final - a.r.final; });
    var byPct = rows.slice().sort(function (a, b) { return b.pct - a.pct; });
    $("pge-ex-title").textContent = "How much has been spent, " + when;
    $("pge-ex-subtitle").textContent = "Obligations recognised, % of each policy's final appropriations" +
      (ex.full_year ? "" : "; dashed, an even pace (a twelfth of the year a month)");
    render({ id: "pge-ex", kind: "hbar", unit: "%", decimals: 0, x_title: "", freq: "A",
             ref_lines: [{ y: +(t.obligations / t.final * 100).toFixed(2), label: "All policies" }].concat(
               ex.full_year ? [] : [{ y: +(ex.month / 12 * 100).toFixed(2), label: "Even pace", dash: "dash" }]),
             series: [{ name: "Spent", x: byPct.map(function (x) { return short(x.r.label); }), y: byPct.map(function (x) { return +x.pct.toFixed(2); }) }] });
    $("pge-ex-caption").textContent = "The State's budget, " + when + " · € bn";
    var html = rows.map(function (x) {
      var r = x.r, ch = r.initial ? (r.final / r.initial - 1) * 100 : null;
      return '<tr class="bx-row" data-pace="p:' + r.code + '" tabindex="0"><th scope="row">' + r.label + '</th><td class="num">' + bn(r.initial) + '</td><td class="num">' + bn(r.final) + '</td><td class="num">' +
             (ch === null ? "–" : (ch > 0 ? "+" : ch < 0 ? "−" : "") + Math.abs(ch).toFixed(1) + "%") + '</td><td class="num">' + bn(r.obligations) +
             '</td><td class="num">' + x.pct.toFixed(1) + "%</td></tr>";
    }).join("");
    var chT = (t.final / t.initial - 1) * 100;
    html += '<tr class="bx-total"><th scope="row">Total</th><td class="num">' + bn(t.initial) + '</td><td class="num">' + bn(t.final) + '</td><td class="num">' +
            (chT > 0 ? "+" : "−") + Math.abs(chT).toFixed(1) + '%</td><td class="num">' + bn(t.obligations) + '</td><td class="num">' +
            (t.obligations / t.final * 100).toFixed(1) + "%</td></tr>";
    $("pge-ex-table").querySelector("tbody").innerHTML = html;
    drawPace(ex);
    drawDetail(ex, when);
  }

  // ---------------------------------------------------------------- the pace of spending
  // A policy's or chapter's obligations to date against its final appropriations, month by month, beside an
  // even pace and the year before (chapters have it month by month; policies only from the kept workbooks).
  var MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                     "November", "December"];
  var pace = { item: "p:TOTAL", view: "pct" };
  function given(v) { return v !== null && v !== undefined; }
  function paceOf(year, key) {
    var y = S.pace && S.pace[year], part = key.charAt(0) === "p" ? "policies" : "chapters";
    var row = y && y[part] ? y[part][key.slice(2)] : null;
    return row && row.final.some(function (v) { return v > 0; }) ? row : null;
  }
  function lastMonth(values) {
    var n = values.length;
    while (n && !given(values[n - 1])) n--;
    return n;
  }
  function paceItems() {
    var any = function (key) { return Object.keys(S.pace).some(function (y) { return paceOf(+y, key); }); };
    var opt = function (key, label) { return '<option value="' + key + '">' + label + "</option>"; };
    var group = function (title, list, prefix) {
      var html = list.filter(function (it) { return it.code !== "TOTAL" && any(prefix + it.code); })
        .map(function (it) { return opt(prefix + it.code, it.label); }).join("");
      return html ? '<optgroup label="' + title + '">' + html + "</optgroup>" : "";
    };
    return (any("p:TOTAL") ? opt("p:TOTAL", "The State's whole budget") : "") + group("Spending policies", S.pace_items.policies, "p:") +
           group("Chapters", S.pace_items.chapters, "c:");
  }

  function drawPace(ex) {
    var sel = $("pge-pace-item");
    if (!sel || !S.pace || !Object.keys(S.pace).length) return;
    if (!sel.options.length) sel.innerHTML = paceItems();
    var y = ex.year;
    if (!paceOf(y, pace.item)) pace.item = paceOf(y, "p:TOTAL") ? "p:TOTAL" : "c:nonfinancial";
    sel.value = pace.item;
    var now = paceOf(y, pace.item), before = paceOf(y - 1, pace.item);
    if (!now || !sel.options.length) { $("pge-pace-facts").innerHTML = ""; return; }
    Array.prototype.forEach.call(document.querySelectorAll("[data-pace-view]"), function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-pace-view") === pace.view));
    });
    var label = sel.options[sel.selectedIndex].text;
    var n = lastMonth(now.obligations), spent = now.obligations[n - 1], budget = now.final[n - 1];
    var share = spent / budget * 100, even = n / 12 * 100, gap = spent - budget * n / 12;
    var facts = [fact("Spent to the end of " + MONTH_NAMES[n - 1] + " " + y, share.toFixed(1) + "% of the budget",
                      "an even pace is " + even.toFixed(1) + "%; €" + bn(spent) + " bn of €" + bn(budget) + " bn"),
                 fact(gap >= 0 ? "Ahead of an even pace" : "Behind an even pace", "€" + Math.abs(gap / 1000).toFixed(1) + " bn",
                      "obligations against a twelfth of the budget a month")];
    if (before && given(before.obligations[n - 1]) && before.final[n - 1]) {
      facts.push(fact("A year earlier", (before.obligations[n - 1] / before.final[n - 1] * 100).toFixed(1) + "%",
                      "spent by the end of " + MONTH_NAMES[n - 1] + " " + (y - 1)));
    } else if (before && given(before.obligations[11]) && before.final[11]) {
      facts.push(fact((y - 1) + " in full", (before.obligations[11] / before.final[11] * 100).toFixed(1) + "%",
                      "of its final budget spent by December"));
    }
    $("pge-pace-facts").innerHTML = facts.join("");

    var upTo = function (values) { var k = lastMonth(values); return { x: MONTHS.slice(0, k), y: values.slice(0, k) }; };
    var series = [];
    var add = function (name, values, style) {
      var cut = upTo(values);
      if (cut.y.some(given)) series.push(Object.assign({ name: name, x: cut.x, y: cut.y }, style));
    };
    var ratio = function (row) {
      return row.obligations.map(function (v, i) { return given(v) && row.final[i] ? +(v / row.final[i] * 100).toFixed(2) : null; });
    };
    var inBn = function (values) { return values.map(function (v) { return given(v) ? +(v / 1000).toFixed(2) : null; }); };
    if (pace.view === "pct") {
      add("Even pace", MONTHS.map(function (_, i) { return +((i + 1) / 12 * 100).toFixed(2); }), { color: "muted", dash: "dot" });
      add(String(y), ratio(now), { slot: 1 });
      if (before) add(String(y - 1), ratio(before), { slot: 1, dash: "dot" });
    } else {
      add("Budget, " + y, inBn(now.final), { color: "ink" });
      add("Even pace", now.final.map(function (v, i) { return given(v) ? +(v * (i + 1) / 12 / 1000).toFixed(2) : null; }), { color: "muted", dash: "dot" });
      add("Spent, " + y, inBn(now.obligations), { slot: 1 });
      if (before) add("Spent, " + (y - 1), inBn(before.obligations), { slot: 1, dash: "dot" });
    }
    $("pge-pace-title").textContent = label + ": the pace of spending, " + y;
    $("pge-pace-subtitle").textContent = pace.view === "pct"
      ? "Obligations recognised to date, % of the final appropriations at each month's end; dotted, an even pace" + (before ? " and " + (y - 1) : "")
      : "€ bn: the final appropriations, the obligations recognised to date and an even pace";
    render({ id: "pge-pace", kind: "line", x_kind: "category", unit: pace.view === "pct" ? "%" : "", decimals: 1,
             freq: "A", series: series });
  }

  // ---------------------------------------------------------------- the rest of the execution report
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function pct(a, b) { return a === null || a === undefined || !b ? "–" : (a / b * 100).toFixed(1) + "%"; }
  function growth(a, b) {
    if (a === null || a === undefined || !b) return "–";
    var c = (a / b - 1) * 100;
    return (c > 0 ? "+" : c < 0 ? "−" : "") + Math.abs(c).toFixed(1) + "%";
  }
  function signedBn(v) { return v === null || v === undefined ? "–" : (v < 0 ? "−€" : "+€") + Math.abs(v / 1000).toFixed(1) + " bn"; }
  function fill(id, html) { var el = $(id); if (el) el.querySelector("tbody").innerHTML = html; }
  function fact(label, value, sub) {
    return '<div class="fact"><span class="fact-label">' + label + '</span><span class="fact-value">' + value +
           '</span><span class="fact-sub">' + sub + "</span></div>";
  }
  function row(cells, cls, indent) {
    return "<tr" + (cls ? ' class="' + cls + '"' : "") + '><th scope="row"' + (indent ? ' class="indent-' + indent + '"' : "") + ">" + cells[0] + "</th>" +
           cells.slice(1).map(function (c) { return '<td class="num">' + c + "</td>"; }).join("") + "</tr>";
  }

  // The pace: the item, the measure, and a policy picked from the table above.
  function currentEx() { return S.execution.filter(function (e) { return e.year === state.exYear; })[0] || S.execution[0]; }
  if ($("pge-pace-item")) {
    $("pge-pace-item").addEventListener("change", function (e) { pace.item = e.target.value; drawPace(currentEx()); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-pace-view]"), function (b) {
      b.addEventListener("click", function () { pace.view = b.getAttribute("data-pace-view"); drawPace(currentEx()); });
    });
    var choose = function (row) {
      if (!paceOf(currentEx().year, row.getAttribute("data-pace"))) return;
      pace.item = row.getAttribute("data-pace");
      drawPace(currentEx());
      $("bx-pge-pace").scrollIntoView({ block: "start" });
    };
    $("pge-ex-table").addEventListener("click", function (e) { var row = e.target.closest("tr[data-pace]"); if (row) choose(row); });
    $("pge-ex-table").addEventListener("keydown", function (e) {
      var row = e.target.closest("tr[data-pace]");
      if (row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); choose(row); }
    });
  }

  // A year's month-by-month totals: from its own workbooks, or from the next year's "a year earlier" columns.
  function path(year, key) {
    var own = S.months[year], next = S.months[year + 1];
    return MONTHS.map(function (_, i) {
      var v = own && own[key] ? own[key][i] : null;
      if ((v === null || v === undefined) && next && next[key + "_prev"]) v = next[key + "_prev"][i];
      return v === undefined ? null : v;
    });
  }

  function drawDetail(ex, when) {
    var d = ex.detail || {};
    var y = ex.year;
    if ($("chart-pge-path")) {
      var last = ex.full_year ? 12 : ex.month;
      var names = MONTHS.slice(0, last);
      var cut = function (a) { return a.slice(0, last).map(function (v) { return v === null ? null : +(v / 1000).toFixed(2); }); };
      render({ id: "pge-path", kind: "line", x_kind: "category", unit: "", decimals: 1, freq: "A",
               series: [{ name: "Revenue " + y, x: names, y: cut(path(y, "revenue")), slot: 1 },
                        { name: "Revenue " + (y - 1), x: names, y: cut(path(y - 1, "revenue")), slot: 1, dash: "dot" },
                        { name: "Spending " + y, x: names, y: cut(path(y, "spending")), slot: 2 },
                        { name: "Spending " + (y - 1), x: names, y: cut(path(y - 1, "spending")), slot: 2, dash: "dot" }] });
      $("pge-path-title").textContent = "Revenue and spending so far, " + y;
      $("pge-path-subtitle").textContent = "€ bn, added up from January; dotted, " + (y - 1);
      render({ id: "pge-cash", kind: "line", x_kind: "category", unit: "", decimals: 1, freq: "A", ref_lines: [{ y: 0, label: "" }],
               series: [{ name: String(y), x: names, y: cut(path(y, "cash")), color: "ink" },
                        { name: String(y - 1), x: names, y: cut(path(y - 1, "cash")), color: "muted", dash: "dot" }] });
      $("pge-cash-title").textContent = "Cash balance so far, " + y;
      $("pge-cash-subtitle").textContent = "€ bn, collected less paid since January (negative: a deficit)";
      var c = d.cash || {}, facts = [];
      if (c.deficit) facts.push(fact("Cash balance, " + when, signedBn(c.deficit.value), "a year earlier " + signedBn(c.deficit.prev)));
      if (c.borrowing) {
        facts.push(fact("Net borrowing need", "€" + Math.abs(c.borrowing.value / 1000).toFixed(1) + " bn",
                        "a year earlier €" + Math.abs(c.borrowing.prev / 1000).toFixed(1) + " bn"));
      }
      var nfR = (d.revenue || []).filter(function (r) { return r.code === "nonfinancial"; })[0];
      var nfS = (d.chapters || []).filter(function (r) { return r.code === "nonfinancial"; })[0];
      if (nfR) facts.push(fact("Revenue due", "€" + bn(nfR.rights) + " bn", growth(nfR.rights, nfR.rights_prev) + " on a year earlier"));
      if (nfS) facts.push(fact("Spending", "€" + bn(nfS.obligations) + " bn", growth(nfS.obligations, nfS.obligations_prev) + " on a year earlier"));
      $("pge-path-facts").innerHTML = facts.join("");
    }

    $("pge-rev-caption").textContent = "The State's revenue, " + when + " · € bn";
    fill("pge-rev-table", (d.revenue || []).map(function (r) {
      var total = r.code === "nonfinancial" || r.code === "total";
      return row([r.label, bn(r.forecast), bn(r.rights), bn(r.collected), pct(r.rights, r.forecast), growth(r.collected, r.collected_prev)],
                 total ? "bx-total" : "", r.indent);
    }).join(""));

    $("pge-tax-caption").textContent = "Net collection, " + when + " · € bn";
    fill("pge-tax-table", (d.taxes || []).map(function (r) {
      return row([r.label, bn(r.collected), bn(r.regions), bn(r.local), bn(r.state), growth(r.collected, r.collected_prev)],
                 r.code === "nonfinancial" ? "bx-total" : "");
    }).join(""));

    $("pge-ch-caption").textContent = "The State's spending by chapter, " + when + " · € bn";
    fill("pge-ch-table", (d.chapters || []).map(function (r) {
      var total = r.code === "nonfinancial" || r.code === "total";
      return row([r.label, bn(r.final), bn(r.committed), bn(r.obligations), pct(r.obligations, r.final), growth(r.obligations, r.obligations_prev)],
                 total ? "bx-total" : "");
    }).join(""));

    var mrr = d.mrr;
    $("pge-mrr-caption").textContent = "Recovery and Resilience Facility, " + when + " · € bn";
    var mrrRows = mrr ? mrr.rows.filter(function (r) { return r.credits > 0 || r.obligations > 0; }).map(function (r) {
      return row([r.label, bn(r.credits), bn(r.committed), bn(r.obligations), pct(r.obligations, r.credits), bn(r.payments)]);
    }) : [];
    if (mrr && mrr.total) {
      var t = mrr.total;
      mrrRows.push(row(["Total", bn(t.credits), bn(t.committed), bn(t.obligations), pct(t.obligations, t.credits), bn(t.payments)], "bx-total"));
    }
    fill("pge-mrr-table", mrrRows.join(""));

    $("pge-tr-caption").textContent = "Transfers in the State's budget, " + when + " · € bn";
    var tr = d.transfers || [];
    var sum = function (k) { return tr.reduce(function (s, r) { return s + (r[k] || 0); }, 0); };
    var trRows = tr.map(function (r) {
      return row([r.label, bn(r.final), bn(r.obligations), pct(r.obligations, r.final), bn(r.obligations_prev), growth(r.obligations, r.obligations_prev)]);
    });
    if (tr.length) {
      trRows.push(row(["Total", bn(sum("final")), bn(sum("obligations")), pct(sum("obligations"), sum("final")), bn(sum("obligations_prev")),
                       growth(sum("obligations"), sum("obligations_prev"))], "bx-total"));
    }
    fill("pge-tr-table", trRows.join(""));
  }

  // ---------------------------------------------------------------- events
  Array.prototype.forEach.call(document.querySelectorAll("[data-pge-kind]"), function (b) {
    b.addEventListener("click", function () {
      state.kind = b.getAttribute("data-pge-kind"); state.selected = [];
      Array.prototype.forEach.call(document.querySelectorAll("[data-pge-kind]"), function (x) {
        x.setAttribute("aria-pressed", String(x === b));
      });
      draw();
    });
  });
  $("pge-measure").addEventListener("change", function (e) { state.measure = e.target.value; draw(); });
  $("pge-year").addEventListener("change", function (e) { state.year = +e.target.value; draw(); });
  $("pge-base").addEventListener("change", function (e) { state.base = +e.target.value; draw(); });
  if ($("pge-ex-year")) $("pge-ex-year").addEventListener("change", function (e) { state.exYear = +e.target.value; drawExecution(); });
  function toggle(code) {
    var i = state.selected.indexOf(code);
    if (i >= 0) state.selected.splice(i, 1);
    else { state.selected.push(code); if (state.selected.length > 3) state.selected.shift(); }
    draw();
  }
  $("pge-table").addEventListener("click", function (e) { var row = e.target.closest("tr.bx-row"); if (row) toggle(row.getAttribute("data-code")); });
  $("pge-table").addEventListener("keydown", function (e) {
    var row = e.target.closest("tr.bx-row");
    if (row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggle(row.getAttribute("data-code")); }
  });

  draw();
})();
