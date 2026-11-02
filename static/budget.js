// Macroscope Spain: the Budget explorer (site/budget-explorer.html). Spending by function and by type, and
// revenue by type, for each administration since 1995, from data/budget.js (econpulse/budget.py: the IGAE's
// national accounts). Values arrive in € mn by year; the measures (constant prices, % of GDP, per person,
// share of the total) are worked out here. Charts are drawn by the site's own renderer (EP.render). The reader
// picks up to six lines over time (items, or communities), each keeping its colour while it stays picked, and
// compares two years, adjusted for inflation when the measure is in euros.
(function () {
  "use strict";

  var B = window.EP && window.EP.budget;
  var render = window.EP && window.EP.render;
  if (!B || !render) return;

  var Y = B.years;
  var MEASURES = {
    eur: { label: "€ bn", unit: "", decimals: 1, suffix: " bn", prefix: "€" },
    real: { label: "€ bn at " + B.price_year + " prices", unit: "", decimals: 1, suffix: " bn", prefix: "€" },
    gdp: { label: "% of GDP", unit: "%", decimals: 2, suffix: "%", prefix: "" },
    person: { label: "€ a person at " + B.price_year + " prices", unit: "€", decimals: 0, suffix: "", prefix: "€" },
    share: { label: "% of the total", unit: "%", decimals: 1, suffix: "%", prefix: "" }
  };
  var VIEW_NAMES = { "function": "Spending by function", type: "Spending by type", revenue: "Revenue" };
  var MAX_LINES = 6;
  // selected and regions: null until chosen, for the defaults (the three largest items, communities).
  var state = { level: B.levels[0].id, view: "function", measure: "eur", exclude: false, year: null, base: null,
                parent: null, selected: null, slots: {}, total: true, cmp: null, regions: null, rslots: {}, all: true };

  function $(id) { return document.getElementById(id); }
  function iso(year) { return year + "-01-01"; }
  function lv() {
    for (var i = 0; i < B.levels.length; i++) { if (B.levels[i].id === state.level) return B.levels[i]; }
    return B.levels[0];
  }
  function minus(a, b) {
    return a.map(function (v, k) { return v === null || v === undefined ? null : v - ((b && b[k]) || 0); });
  }
  function find(list, code) {
    for (var i = 0; i < list.length; i++) { if (list[i].code === code) return list[i]; }
    return null;
  }

  // ---------------------------------------------------------------- picked lines
  // Each picked line keeps its palette slot while it stays picked; slots 4 to 6 are drawn dashed.
  function slotsFor(slots, picked) {
    Object.keys(slots).forEach(function (c) { if (picked.indexOf(c) < 0) delete slots[c]; });
    picked.forEach(function (c) {
      if (slots[c]) return;
      var used = Object.keys(slots).map(function (k) { return slots[k]; });
      for (var n = 1; n <= MAX_LINES; n++) { if (used.indexOf(n) < 0) { slots[c] = n; break; } }
    });
  }
  function line(name, ys, conv, slot) {
    return { name: name, x: ys.map(iso), y: ys.map(function (y) { return at(conv, y); }), slot: slot, dash: slot > 3 ? "dash" : "solid" };
  }
  function swatch(slot) {
    return slot > 3 ? "background:transparent;border:2px dashed var(--series-" + slot + ")" : "background:var(--series-" + slot + ")";
  }
  // A row of chips: the extras first (a total, in text ink), then the items.
  function chips(holder, list, picked, slots, extras) {
    var full = picked.length >= MAX_LINES;
    var html = (extras || []).map(function (e) {
      return '<button type="button" class="chip" data-pick="' + e.code + '" aria-pressed="' + e.on + '"><span class="chip-swatch" aria-hidden="true" style="' +
             (e.on ? "background:var(--text)" : "") + '"></span>' + e.label + "</button>";
    }).join("") + list.map(function (it) {
      var on = picked.indexOf(it.code) >= 0, off = !on && full;
      return '<button type="button" class="chip" data-pick="' + it.code + '" aria-pressed="' + on + '" aria-disabled="' + off + '"' +
             (off ? ' title="Up to ' + MAX_LINES + ' at a time: untick one first"' : "") + '><span class="chip-swatch" aria-hidden="true" style="' +
             (on ? swatch(slots[it.code]) : "") + '"></span>' + short(it.label) + "</button>";
    }).join("");
    if (holder.innerHTML !== html) holder.innerHTML = html;
  }
  function togglePicked(list, code) {
    var i = list.indexOf(code);
    if (i >= 0) list.splice(i, 1);
    else if (list.length < MAX_LINES) list.push(code);
  }

  // ---------------------------------------------------------------- what the current view lists
  function flowKey() { return state.view === "function" ? B.transfer_function : "transfers"; }
  function showFlows() { return lv().transfers && !state.exclude; }

  function hasData(v) { return v && v.some(function (x) { return x; }); }

  // The parts an item opens into, if this administration has figures for them.
  function childrenOf(it, level) {
    if (state.view === "revenue" && it.code === "products") {
      return level.product_items.some(function (p) { return hasData(level.products[p.code]); }) ? level.product_items : null;
    }
    if (state.view !== "function" || !it.children || !it.children.length) return null;
    return it.children.some(function (c) { return hasData(level["function"][c.code]); }) ? it.children : null;
  }

  function items(levelArg) {
    var level = levelArg || lv(), out = [];
    var list, values;
    if (state.view === "function") {
      list = state.parent ? find(B.functions, state.parent).children : B.functions;
      values = level["function"];
    } else if (state.view === "type") {
      list = B.types; values = level.type;
    } else {
      list = state.parent ? level.product_items : B.revenues;
      values = state.parent ? level.products : level.revenue;
    }
    var flows = level.transfers && !state.exclude;
    list.forEach(function (it) {
      var v = values[it.code], label = it.label;
      if (!hasData(v)) return;
      if (it.code === flowKey() && !flows) return;
      // General public services hold the transfers to other administrations (group 01.8), where it is published.
      if (state.view === "function" && !state.parent && it.code === "01" && !flows && hasData(values[B.transfer_function])) {
        v = minus(v, values[B.transfer_function]);
        label += ", without transfers";
      }
      out.push({ code: it.code, label: label, values: v, children: state.parent ? null : childrenOf(it, level) });
    });
    return out;
  }

  // The total the items add up to: the administration's, or the parent's when drilled in.
  function total(levelArg) {
    var level = levelArg || lv();
    var flows = level.transfers && !state.exclude;
    if (state.view === "function") {
      if (state.parent) {
        var p = level["function"][state.parent];
        return state.parent === "01" && !flows ? minus(p, level["function"][B.transfer_function]) : p;
      }
      return flows ? level["function"].TOTAL : minus(level["function"].TOTAL, level["function"][B.transfer_function]);
    }
    if (state.view === "type") return flows ? level.type.TOTAL : minus(level.type.TOTAL, level.type.transfers);
    if (state.parent) return level.revenue[state.parent];
    return flows ? level.revenue.TOTAL : minus(level.revenue.TOTAL, level.revenue.transfers);
  }

  function years() {
    var t = total();
    return Y.filter(function (y, k) { return t[k] !== null && t[k] !== undefined; });
  }

  function provisional(year) {
    var p = lv().provisional[state.view === "function" ? "function" : "accounts"] || [];
    return p.indexOf(year) >= 0;
  }

  // ---------------------------------------------------------------- measures
  // A community's figures are set against its own GDP and population; the others against Spain's.
  function convert(values, tot, levelArg, measureArg) {
    var level = levelArg || lv();
    var gdp = level.gdp || B.gdp, population = level.population || B.population;
    return values.map(function (v, k) {
      if (v === null || v === undefined) return null;
      switch (measureArg || state.measure) {
        case "eur": return v / 1000;
        case "real": return B.prices[k] ? v / 1000 * 100 / B.prices[k] : null;
        case "gdp": return gdp[k] ? v / gdp[k] * 100 : null;
        case "person": return population[k] && B.prices[k] ? v * 1e6 / population[k] * 100 / B.prices[k] : null;
        case "share": return tot && tot[k] ? v / tot[k] * 100 : null;
      }
      return null;
    });
  }
  function at(series, year) { var k = Y.indexOf(year); return k < 0 || !series ? null : series[k]; }
  function fmt(v, m) {
    if (v === null || v === undefined || isNaN(v)) return "–";
    var d = m.decimals;
    var s = Math.abs(v).toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
    return (v < 0 ? "−" : "") + m.prefix + s + m.suffix;
  }
  function change(now, then, measureArg) {
    var ms = measureArg || state.measure;
    if (now === null || then === null || now === undefined || then === undefined) return "–";
    if (ms === "gdp" || ms === "share") {
      var d = now - then;
      return (d > 0 ? "+" : d < 0 ? "−" : "") + Math.abs(d).toFixed(ms === "gdp" ? 2 : 1) + " pp";
    }
    if (!then) return "–";
    var c = (now / then - 1) * 100;
    return (c > 0 ? "+" : c < 0 ? "−" : "") + Math.abs(c).toFixed(1) + "%";
  }
  function short(label) { return label.length > 44 ? label.slice(0, 42) + "…" : label; }
  // Two years compare in the chosen measure, except euros of the day, which become constant prices.
  function twoMeasure() { return state.measure === "eur" ? "real" : state.measure; }
  function given(v) { return v !== null && v !== undefined; }
  function twoNote(a, b, ms) { return change(b, a, ms) + (ms === "real" || ms === "person" ? " after inflation" : ""); }

  // ---------------------------------------------------------------- drawing
  function draw() {
    var m = MEASURES[state.measure];
    var list = items(), tot = total();
    var ys = years();
    if (ys.indexOf(state.year) < 0) state.year = ys[ys.length - 1];
    if (ys.indexOf(state.base) < 0) state.base = ys[Math.max(0, ys.length - 11)];
    fillYears(ys);
    var before = state.selected;
    state.selected = (before || []).filter(function (c) { return find(list, c); });
    if (before === null || (before.length && !state.selected.length)) {
      state.selected = list.slice().sort(function (a, b) { return (at(b.values, state.year) || 0) - (at(a.values, state.year) || 0); })
        .slice(0, 3).map(function (it) { return it.code; });
    }
    var rows = list.map(function (it) {
      var conv = convert(it.values, tot);
      return { it: it, conv: conv, now: at(conv, state.year), then: at(conv, state.base), real: convert(it.values, tot, null, "real"),
               share: tot ? (at(it.values, state.year) || 0) / (at(tot, state.year) || NaN) * 100 : null };
    }).sort(function (a, b) { return (b.now || 0) - (a.now || 0); });
    var totConv = convert(tot, tot);
    var where = state.parent ? (state.view === "function" ? find(B.functions, state.parent).label : find(B.revenues, state.parent).label) : VIEW_NAMES[state.view];
    var yearLabel = state.year + (provisional(state.year) ? " (provisional)" : "");

    facts(tot, list);
    crumbs();
    $("bx-about").textContent = lv().about;

    // The mix in the chosen year.
    var picked = find(list, state.selected[0]);
    $("bx-mix-title").textContent = where + ", " + yearLabel;
    $("bx-mix-subtitle").textContent = lv().short + " · " + m.label;
    render({ id: "bx-mix", kind: "hbar", unit: m.unit, decimals: m.decimals, x_title: "",
             highlight: picked ? short(picked.label) : null, freq: "A",
             series: [{ name: where, x: rows.map(function (r) { return short(r.it.label); }), y: rows.map(function (r) { return r.now === null ? 0 : +r.now.toFixed(4); }) }] });

    // The picked items over time, with the total.
    slotsFor(state.slots, state.selected);
    var totalName = state.parent ? where : "Total";
    chips($("bx-picks"), list, state.selected, state.slots,
          state.measure === "share" ? [] : [{ code: "__total", label: totalName, on: state.total }]);
    var series = [];
    var totalLine = { name: totalName, x: ys.map(iso), y: ys.map(function (y) { return at(totConv, y); }), color: "ink" };
    if (state.total && state.measure !== "share") series.push(totalLine);
    state.selected.forEach(function (code) {
      var r = rows.filter(function (x) { return x.it.code === code; })[0];
      if (r) series.push(line(short(r.it.label), ys, r.conv, state.slots[code]));
    });
    if (!series.length) series.push(totalLine);
    $("bx-trend-title").textContent = where + " over time";
    $("bx-trend-subtitle").textContent = lv().short + " · " + m.label;
    render({ id: "bx-trend", kind: "line", unit: m.unit === "%" ? "%" : "", decimals: m.decimals, freq: "A", series: series });

    // The two years compared, item by item.
    var ms = twoMeasure(), m2 = MEASURES[ms];
    var two = list.map(function (it) {
      var conv = convert(it.values, tot, null, ms);
      return { label: short(it.label), a: at(conv, state.base), b: at(conv, state.year) };
    }).filter(function (r) { return given(r.a) && given(r.b); }).sort(function (x, y) { return y.b - x.b; });
    two.forEach(function (r) { r.note = twoNote(r.a, r.b, ms); });
    var tot2 = convert(tot, tot, null, ms);
    $("bx-two-title").textContent = where + ", " + state.base + " and " + yearLabel;
    $("bx-two-subtitle").textContent = lv().short + " · " + m2.label +
      (ms !== "share" && given(at(tot2, state.base)) ? " · total " + fmt(at(tot2, state.base), m2) + " → " + fmt(at(tot2, state.year), m2) +
       " (" + change(at(tot2, state.year), at(tot2, state.base), ms) + ")" : "");
    render({ id: "bx-two", kind: "dumbbell", unit: m2.unit, decimals: m2.decimals, x_title: state.view === "function" ? "Function" : state.view === "type" ? "Type" : "Revenue",
             a_name: String(state.base), b_name: String(state.year), rows: two });

    table(rows, totConv, m, where, yearLabel, convert(tot, tot, null, "real"));
    compare(m, yearLabel);
    writeHash();
  }

  // ---------------------------------------------------------------- the communities side by side
  var COMMUNITIES = B.levels.filter(function (l) { return l.community; });
  var REGIONS = find(B.levels.map(function (l) { return { code: l.id, level: l }; }), "regions");

  function compareChoices() {
    var list = state.view === "function" ? B.functions : state.view === "type" ? B.types : B.revenues;
    return [{ code: "TOTAL", label: state.view === "revenue" ? "All revenue" : "All spending" }].concat(list.filter(function (it) {
      return COMMUNITIES.some(function (c) {
        var t = state.view === "function" ? c["function"] : state.view === "type" ? c.type : c.revenue;
        return hasData(t[it.code]);
      });
    }));
  }

  function compareValues(level, code, measureArg) {
    var saved = state.parent;
    state.parent = null;
    var tot = total(level), values;
    if (code === "TOTAL") values = tot;
    else {
      var it = find(items(level), code);
      values = it ? it.values : null;
    }
    state.parent = saved;
    return values ? convert(values, tot, level, measureArg) : null;
  }
  function latest(series) {
    for (var k = series.length - 1; k >= 0; k--) { if (given(series[k])) return series[k]; }
    return 0;
  }

  function compareOverTime(label, all) {
    if (state.regions === null) {
      state.regions = COMMUNITIES.slice().sort(function (a, b) { return latest(b.population) - latest(a.population); })
        .slice(0, 3).map(function (c) { return c.id; });
      if (lv().community && state.regions.indexOf(lv().id) < 0) state.regions.push(lv().id);
    }
    var ms = twoMeasure(), m2 = MEASURES[ms];
    slotsFor(state.rslots, state.regions);
    // All communities together only as a rate (per person, % of GDP, a share): in euros it would dwarf the rest.
    var allRate = all && ms !== "real";
    chips($("bx-cmp-picks"), COMMUNITIES.map(function (c) { return { code: c.id, label: c.name }; }), state.regions, state.rslots,
          allRate ? [{ code: "__all", label: "All communities", on: state.all }] : []);
    var lines = [];
    var allValues = allRate ? compareValues(REGIONS.level, state.cmp, ms) : null;
    state.regions.forEach(function (id) {
      var c = find(COMMUNITIES.map(function (l) { return { code: l.id, level: l }; }), id);
      var v = c ? compareValues(c.level, state.cmp, ms) : null;
      if (v) lines.push({ name: c.level.name, values: v, slot: state.rslots[id] });
    });
    var ys = Y.filter(function (y) {
      return (allValues && state.all && given(at(allValues, y))) || lines.some(function (l) { return given(at(l.values, y)); });
    });
    var series = [];
    if (allValues && state.all) series.push({ name: "All communities", x: ys.map(iso), y: ys.map(function (y) { return at(allValues, y); }), color: "ink" });
    lines.forEach(function (l) { series.push(line(l.name, ys, l.values, l.slot)); });
    $("bx-cmp-trend-title").textContent = label + " over time";
    $("bx-cmp-trend-subtitle").textContent = (lines.length ? "Picked communities" : "Pick communities below the chart") + " · " + m2.label;
    if (series.length && ys.length) {
      render({ id: "bx-cmp-trend", kind: "line", unit: m2.unit === "%" ? "%" : "", decimals: m2.decimals, freq: "A", series: series });
    }

    var two = COMMUNITIES.map(function (c) {
      var v = compareValues(c, state.cmp, ms);
      return { label: c.name, a: v ? at(v, state.base) : null, b: v ? at(v, state.year) : null, highlight: c.id === state.level };
    }).filter(function (r) { return given(r.a) && given(r.b); }).sort(function (x, y) { return y.b - x.b; });
    two.forEach(function (r) { r.note = twoNote(r.a, r.b, ms); });
    $("bx-cmp-two-title").textContent = label + ", " + state.base + " and " + state.year;
    $("bx-cmp-two-subtitle").textContent = (two.length ? "The 17 communities" : "No figures for both years") + " · " + m2.label;
    render({ id: "bx-cmp-two", kind: "dumbbell", unit: m2.unit, decimals: m2.decimals, x_title: "Community",
             a_name: String(state.base), b_name: String(state.year), rows: two });
  }

  function compare(m, yearLabel) {
    var box = $("bx-compare");
    if (!box) return;
    var show = COMMUNITIES.length && (lv().community || lv().id === "regions");
    box.hidden = !show;
    if (!show) return;
    var sel = $("bx-cmp-item"), choices = compareChoices();
    if (!find(choices, state.cmp)) state.cmp = state.view === "function" ? "07" : "TOTAL";
    if (!find(choices, state.cmp)) state.cmp = "TOTAL";
    var want = choices.map(function (c) { return '<option value="' + c.code + '"' + (c.code === state.cmp ? " selected" : "") + ">" + c.label + "</option>"; }).join("");
    if (sel.innerHTML !== want) sel.innerHTML = want;
    sel.value = state.cmp;
    var label = find(choices, state.cmp).label;
    var rows = COMMUNITIES.map(function (c) {
      var v = compareValues(c, state.cmp);
      return { level: c, now: v ? at(v, state.year) : null, then: v ? at(v, state.base) : null };
    }).filter(function (r) { return r.now !== null && r.now !== undefined; })
      .sort(function (a, b) { return b.now - a.now; });
    var all = REGIONS ? compareValues(REGIONS.level, state.cmp) : null;
    $("bx-cmp-title").textContent = label + ", " + yearLabel;
    $("bx-cmp-subtitle").textContent = "The 17 communities · " + m.label;
    var ref = all && state.measure !== "eur" && state.measure !== "real" ? at(all, state.year) : null;
    render({ id: "bx-cmp", kind: "hbar", unit: m.unit, decimals: m.decimals, x_title: "", freq: "A",
             highlight: lv().community ? lv().name : null,
             ref_lines: ref !== null && ref !== undefined ? [{ y: +ref.toFixed(4), label: "All communities" }] : [],
             series: [{ name: label, x: rows.map(function (r) { return r.level.name; }), y: rows.map(function (r) { return +r.now.toFixed(4); }) }] });
    $("bx-cmp-caption").textContent = label + " · " + m.label;
    $("bx-cmp-col-year").textContent = yearLabel;
    $("bx-cmp-col-base").textContent = state.base;
    var html = rows.map(function (r) {
      return '<tr class="bx-cmp-row' + (r.level.id === state.level ? " highlight-row" : "") + '" data-level="' + r.level.id + '" tabindex="0">' +
             '<th scope="row">' + r.level.name + '</th><td class="num">' + fmt(r.now, m) + '</td><td class="num">' + fmt(r.then, m) +
             '</td><td class="num">' + change(r.now, r.then) + "</td></tr>";
    }).join("");
    if (all) {
      html += '<tr class="bx-total"><th scope="row">All communities</th><td class="num">' + fmt(at(all, state.year), m) +
              '</td><td class="num">' + fmt(at(all, state.base), m) + '</td><td class="num">' + change(at(all, state.year), at(all, state.base)) + "</td></tr>";
    }
    $("bx-cmp-table").querySelector("tbody").innerHTML = html;
    compareOverTime(label, all);
  }

  function facts(tot, list) {
    var k = Y.indexOf(state.year), level = lv(), out = [];
    var gdp = level.gdp || B.gdp, population = level.population || B.population;
    var raw = at(tot, state.year);
    var noun = state.view === "revenue" ? "Revenue" : "Spending";
    if (raw !== null && raw !== undefined) {
      out.push([noun + " in " + state.year, "€" + (raw / 1000).toLocaleString("en-GB", { maximumFractionDigits: 1, minimumFractionDigits: 1 }) + " bn",
                gdp[k] ? (raw / gdp[k] * 100).toFixed(1) + "% of " + (level.community ? "its GDP" : "GDP") : ""]);
      if (population[k]) out.push(["A person", "€" + Math.round(raw * 1e6 / population[k]).toLocaleString("en-GB"), "in " + state.year + ", at that year's prices"]);
    }
    if (level.balance && level.balance[k] !== null && level.balance[k] !== undefined) {
      var bal = level.balance[k];
      out.push(["Balance in " + state.year, (bal >= 0 ? "+€" : "−€") + (Math.abs(bal) / 1000).toFixed(2) + " bn",
                (bal >= 0 ? "a surplus" : "a deficit") + (gdp[k] ? ", " + (Math.abs(bal) / gdp[k] * 100).toFixed(1) + "% of its GDP" : "")]);
    }
    if (level.transfers && !state.parent) {
      var table = state.view === "function" ? level["function"] : state.view === "type" ? level.type : level.revenue;
      var flows = at(table[flowKey()], state.year), all = at(table.TOTAL, state.year);
      if (flows && all) {
        out.push([state.view === "revenue" ? "From other administrations" : "Passed to other administrations",
                  "€" + (flows / 1000).toFixed(1) + " bn", Math.round(flows / all * 100) + "% of the total" + (state.exclude ? ", left out here" : "")]);
      }
    }
    $("bx-facts").innerHTML = out.map(function (f) {
      return '<div class="fact"><span class="fact-label">' + f[0] + '</span><span class="fact-value">' + f[1] +
             '</span><span class="fact-sub">' + f[2] + "</span></div>";
    }).join("");
  }

  function crumbs() {
    var el = $("bx-crumbs");
    if (!state.parent) { el.innerHTML = ""; el.hidden = true; return; }
    el.hidden = false;
    var parent = state.view === "function" ? find(B.functions, state.parent) : find(B.revenues, state.parent);
    el.innerHTML = '<button type="button" class="chart-link" id="bx-up">← All ' + (state.view === "function" ? "functions" : "revenue") +
                   "</button> <span>" + (state.view === "function" ? parent.code + " " : "") + parent.label + "</span>";
    $("bx-up").addEventListener("click", function () { state.parent = null; state.selected = null; draw(); });
  }

  function table(rows, totConv, m, where, yearLabel, totReal) {
    $("bx-table-caption").textContent = where + " · " + lv().short + " · " + m.label;
    $("bx-col-item").textContent = state.view === "function" ? "Function" : state.view === "type" ? "Type" : "Revenue";
    $("bx-col-year").textContent = yearLabel;
    $("bx-col-base").textContent = state.base;
    $("bx-col-change").textContent = state.measure === "gdp" || state.measure === "share" ? "Change" : "Change, %";
    var real = state.measure === "eur";
    $("bx-col-real").hidden = !real;
    var realCell = function (series) {
      return real ? '<td class="num">' + change(at(series, state.year), at(series, state.base), "real") + "</td>" : "";
    };
    var body = $("bx-table").querySelector("tbody");
    var html = rows.map(function (r) {
      var on = state.selected.indexOf(r.it.code) >= 0;
      var open = r.it.children ? ' <button type="button" class="chart-link bx-open" data-open="' + r.it.code + '" aria-label="Open ' + r.it.label + ' into its parts">▸ parts</button>' : "";
      var code = state.view === "function" ? '<span class="period-note">' + r.it.code + " </span>" : "";
      return '<tr class="bx-row' + (on ? " highlight-row" : "") + '" data-code="' + r.it.code + '" tabindex="0" aria-selected="' + on + '">' +
             '<th scope="row">' + code + r.it.label + open + "</th>" +
             '<td class="num">' + fmt(r.now, m) + "</td>" +
             '<td class="num">' + (r.share === null || isNaN(r.share) ? "–" : r.share.toFixed(1) + "%") + "</td>" +
             '<td class="num">' + fmt(r.then, m) + "</td>" +
             '<td class="num">' + change(r.now, r.then) + "</td>" + realCell(r.real) + "</tr>";
    }).join("");
    var tNow = at(totConv, state.year), tThen = at(totConv, state.base);
    if (state.measure !== "share") {
      html += '<tr class="bx-total"><th scope="row">' + (state.parent ? "Total" : "Total" + (state.exclude && lv().transfers ? ", without flows between administrations" : "")) + "</th>" +
              '<td class="num">' + fmt(tNow, m) + '</td><td class="num">100%</td><td class="num">' + fmt(tThen, m) +
              '</td><td class="num">' + change(tNow, tThen) + "</td>" + realCell(totReal) + "</tr>";
    }
    body.innerHTML = html;
  }

  function fillYears(ys) {
    [["bx-year", state.year], ["bx-base", state.base]].forEach(function (pair) {
      var sel = $(pair[0]);
      var want = ys.slice().reverse().map(function (y) { return '<option value="' + y + '"' + (y === pair[1] ? " selected" : "") + ">" + y + (provisional(y) ? " (P)" : "") + "</option>"; }).join("");
      if (sel.innerHTML !== want) sel.innerHTML = want;
      sel.value = String(pair[1]);
    });
  }

  // ---------------------------------------------------------------- state in the address, for sharing
  var touched = false;      // until a control is used, a link to a section (#bx-pge) stays in the address
  function writeHash() {
    if (!touched && location.hash && location.hash.indexOf("level=") < 0) return;
    var h = "level=" + state.level + "&view=" + state.view + "&measure=" + state.measure + "&year=" + state.year +
            "&base=" + state.base + (state.exclude ? "&exclude=1" : "") + (state.parent ? "&parent=" + state.parent : "") +
            "&sel=" + state.selected.join(",") + (state.total ? "" : "&total=0") + (state.cmp ? "&cmp=" + state.cmp : "") +
            (state.regions ? "&regs=" + state.regions.join(",") : "") + (state.all ? "" : "&all=0");
    history.replaceState(null, "", "#" + h);
  }
  function readHash() {
    var h = location.hash.slice(1);
    if (h.indexOf("level=") < 0) return;
    h.split("&").forEach(function (part) {
      var kv = part.split("="), k = kv[0], v = decodeURIComponent(kv[1] || "");
      if (k === "level" && B.levels.some(function (l) { return l.id === v; })) state.level = v;
      if (k === "view" && VIEW_NAMES[v]) state.view = v;
      if (k === "measure" && MEASURES[v]) state.measure = v;
      if (k === "year" || k === "base") state[k] = +v;
      if (k === "exclude") state.exclude = v === "1";
      if (k === "parent") state.parent = v || null;
      if (k === "sel") state.selected = v ? v.split(",") : [];
      if (k === "cmp") state.cmp = v || null;
      if (k === "total") state.total = v !== "0";
      if (k === "all") state.all = v !== "0";
      if (k === "regs") {
        state.regions = (v ? v.split(",") : []).filter(function (id) { return COMMUNITIES.some(function (c) { return c.id === id; }); }).slice(0, MAX_LINES);
      }
    });
  }

  function syncControls() {
    $("bx-level").value = state.level;
    $("bx-measure").value = state.measure;
    $("bx-exclude").checked = state.exclude;
    $("bx-exclude").disabled = !lv().transfers;
    Array.prototype.forEach.call(document.querySelectorAll("[data-bx-view]"), function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-bx-view") === state.view));
    });
  }

  // ---------------------------------------------------------------- events
  ["input", "change"].forEach(function (type) {
    $("bx-level").closest(".bx-controls").parentNode.addEventListener(type, function (e) {
      if (!e.target.closest("#bx-pge")) touched = true;
    }, true);
  });
  document.querySelector(".bx-controls").parentNode.addEventListener("click", function (e) {
    if (e.target.closest("#bx-pge") === null && e.target.closest("button, tr, select, input")) touched = true;
  }, true);
  $("bx-level").addEventListener("change", function (e) { state.level = e.target.value; state.parent = null; syncControls(); draw(); });
  $("bx-measure").addEventListener("change", function (e) { state.measure = e.target.value; draw(); });
  $("bx-year").addEventListener("change", function (e) { state.year = +e.target.value; draw(); });
  $("bx-base").addEventListener("change", function (e) { state.base = +e.target.value; draw(); });
  $("bx-exclude").addEventListener("change", function (e) { state.exclude = e.target.checked; draw(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-bx-view]"), function (b) {
    b.addEventListener("click", function () {
      state.view = b.getAttribute("data-bx-view"); state.parent = null; state.selected = null;
      syncControls(); draw();
    });
  });
  $("bx-table").addEventListener("click", function (e) {
    var open = e.target.closest("[data-open]");
    if (open) { state.parent = open.getAttribute("data-open"); state.selected = null; draw(); return; }
    var row = e.target.closest("tr.bx-row");
    if (!row) return;
    toggle(row.getAttribute("data-code"));
  });
  $("bx-table").addEventListener("keydown", function (e) {
    var row = e.target.closest("tr.bx-row");
    if (row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); toggle(row.getAttribute("data-code")); }
  });
  if ($("bx-cmp-item")) {
    $("bx-cmp-item").addEventListener("change", function (e) { state.cmp = e.target.value; draw(); });
    // A community's row opens that community above.
    var pick = function (row) {
      state.level = row.getAttribute("data-level"); state.parent = null; state.selected = null;
      syncControls(); draw(); $("bx-level").scrollIntoView({ block: "center" });
    };
    $("bx-cmp-table").addEventListener("click", function (e) { var row = e.target.closest("tr.bx-cmp-row"); if (row) pick(row); });
    $("bx-cmp-table").addEventListener("keydown", function (e) {
      var row = e.target.closest("tr.bx-cmp-row");
      if (row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pick(row); }
    });
  }
  function toggle(code) {
    togglePicked(state.selected, code);
    draw();
  }
  $("bx-picks").addEventListener("click", function (e) {
    var b = e.target.closest(".chip");
    if (!b || b.getAttribute("aria-disabled") === "true") return;
    var code = b.getAttribute("data-pick");
    if (code === "__total") state.total = !state.total;
    else togglePicked(state.selected, code);
    draw();
  });
  if ($("bx-cmp-picks")) {
    $("bx-cmp-picks").addEventListener("click", function (e) {
      var b = e.target.closest(".chip");
      if (!b || b.getAttribute("aria-disabled") === "true") return;
      var code = b.getAttribute("data-pick");
      if (code === "__all") state.all = !state.all;
      else togglePicked(state.regions, code);
      draw();
    });
  }

  // A link to the explorer itself (the menus' "the autonomous communities") starts again from what it names.
  window.addEventListener("hashchange", function () {
    if (location.hash.indexOf("level=") < 0) return;
    state.parent = null; state.selected = null; state.cmp = null; state.regions = null; state.total = true; state.all = true;
    readHash();
    syncControls();
    draw();
  });

  readHash();
  syncControls();
  draw();
})();
