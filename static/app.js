// Macroscope Spain: theme toggle and charts.
// Pages are plain HTML; this script only adds the light/dark switch and draws the
// charts from window.EP.charts (written by `python -m econpulse build`).
(function () {
  "use strict";

  var root = document.documentElement;
  var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  // The page's language (Batch 33a: the Spanish site is under es/), and its words for what this script writes.
  var LANG = root.lang === "es" ? "es" : "en";
  var ES = {
    "Time range": "Periodo", "All": "Todo", "All the data": "Todos los datos", "Item": "Concepto", "Change": "Variación",
    "Member": "Miembro", "Stance": "Orientación", "Latest": "Último", "Range over the year": "Rango en el año",
    "Lowest over the year": "Mínimo del año", "Highest over the year": "Máximo del año", "Date": "Fecha", "Period": "Periodo",
    "All points.": "Todos los puntos.", "Latest 12 periods.": "Últimos 12 periodos.", "Link copied": "Enlace copiado",
    "Copy this link:": "Copie este enlace:", "Page": "Página", "Section": "Sección", "Chart": "Gráfico", "Series": "Serie",
    "Loading the index…": "Cargando el índice…", "The search index could not be loaded.": "No se pudo cargar el índice de búsqueda.",
    "On this page": "En esta página", "Sections of this page": "Secciones de esta página", "Top": "Arriba",
    "Back to the top of the page": "Volver al principio de la página", "Reading": "Lectura", " to ": " a ",
    "Copy a link to the section": "Copiar un enlace a la sección", "Countries": "Países"
  };
  function t(s) { return LANG === "es" && ES[s] !== undefined ? ES[s] : s; }

  // Switching language keeps the place on the page (a chart's anchor, an explorer's settings).
  Array.prototype.forEach.call(document.querySelectorAll(".lang-switch a"), function (a) {
    a.addEventListener("click", function () {
      if (location.hash && !a.hasAttribute("aria-current")) a.href = a.getAttribute("href").split("#")[0] + location.hash;
    });
  });

  function currentTheme() {
    return root.getAttribute("data-theme") || (darkQuery.matches ? "dark" : "light");
  }

  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("ep-theme", next); } catch (e) { /* storage blocked: choice lasts this visit */ }
      drawAll();
    });
  }
  darkQuery.addEventListener("change", drawAll);

  // ---------------------------------------------------------------- tab dropdowns
  // Each tab's ▾ opens a list of the sections on that page. The lists live outside the scrolling
  // tab bar, so they are placed under their tab here. Hover opens them where there is a mouse.
  (function () {
    var open = null, timer = null, hover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    function place(item, menu) {
      var r = item.getBoundingClientRect(), w = menu.offsetWidth;
      menu.style.top = Math.round(r.bottom) + "px";
      menu.style.left = Math.round(Math.max(8, Math.min(r.left, window.innerWidth - w - 8))) + "px";
    }
    function close(focusCaret) {
      if (!open) return;
      open.menu.hidden = true;
      open.caret.setAttribute("aria-expanded", "false");
      if (focusCaret) open.caret.focus();
      open = null;
    }
    function show(item, focusFirst) {
      var caret = item.querySelector(".nav-caret"), menu = document.getElementById(item.getAttribute("data-menu"));
      if (!caret || !menu) return;
      if (open && open.menu === menu) return;
      close(false);
      menu.hidden = false;
      place(item, menu);
      caret.setAttribute("aria-expanded", "true");
      open = { item: item, caret: caret, menu: menu };
      if (focusFirst) { var first = menu.querySelector("a"); if (first) first.focus(); }
    }
    Array.prototype.forEach.call(document.querySelectorAll(".nav-item[data-menu^='menu']"), function (item) {
      var caret = item.querySelector(".nav-caret"), menu = document.getElementById(item.getAttribute("data-menu"));
      caret.addEventListener("click", function (e) {
        e.stopPropagation();
        if (open && open.item === item) close(false); else show(item, e.detail === 0);   // keyboard: focus the first link
      });
      if (hover) {
        [item, menu].forEach(function (el) {
          el.addEventListener("mouseenter", function () { clearTimeout(timer); timer = setTimeout(function () { show(item, false); }, 120); });
          el.addEventListener("mouseleave", function () { clearTimeout(timer); timer = setTimeout(function () { if (open && open.item === item) close(false); }, 250); });
        });
      }
      menu.addEventListener("keydown", function (e) {
        var links = Array.prototype.slice.call(menu.querySelectorAll("a")), i = links.indexOf(document.activeElement);
        if (e.key === "Escape") { e.preventDefault(); close(true); }
        else if (e.key === "ArrowDown") { e.preventDefault(); links[(i + 1) % links.length].focus(); }
        else if (e.key === "ArrowUp") { e.preventDefault(); links[(i - 1 + links.length) % links.length].focus(); }
        else if (e.key === "Tab" && ((!e.shiftKey && i === links.length - 1) || (e.shiftKey && i === 0))) close(!e.shiftKey ? false : true);
      });
      menu.addEventListener("click", function (e) { if (e.target.closest("a")) close(false); });
    });
    document.addEventListener("click", function (e) { if (open && !open.menu.contains(e.target)) close(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(true); });
    window.addEventListener("resize", function () { close(false); });
    window.addEventListener("scroll", function () { if (open) place(open.item, open.menu); }, { passive: true });
    var bar = document.querySelector(".site-nav");
    if (bar) bar.addEventListener("scroll", function () { if (open) place(open.item, open.menu); }, { passive: true });
  })();

  // On phones the tab bar scrolls sideways: fade the edge where there are more tabs, and bring the
  // current page's tab into view.
  (function () {
    var bar = document.querySelector(".site-nav");
    if (!bar) return;
    function edges() {
      var scrollable = bar.scrollWidth > bar.clientWidth + 2;
      bar.classList.toggle("more-left", scrollable && bar.scrollLeft > 2);
      bar.classList.toggle("more-right", scrollable && bar.scrollLeft + bar.clientWidth < bar.scrollWidth - 2);
    }
    var current = bar.querySelector('[aria-current="page"]');
    if (current && bar.scrollWidth > bar.clientWidth + 2) {
      var item = current.closest(".nav-item") || current;
      if (item.offsetLeft + item.offsetWidth > bar.clientWidth) bar.scrollLeft = item.offsetLeft - 24;
    }
    edges();
    bar.addEventListener("scroll", edges, { passive: true });
    window.addEventListener("resize", edges);
  })();

  // ---------------------------------------------------------------- charts
  var specs = (window.EP && window.EP.charts) || [];
  var MONTHS = LANG === "es" ? ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                               : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  // ---------------------------------------------------------------- chosen comparators (International page)
  // Charts flagged `pick` carry every country's series, tagged `country` (or `countries`, for a central
  // bank). The reader picks any number of comparators (Batch 34a): they are drawn beside Spain, which is in
  // text ink. Each country has its own colour and line style (econpulse/peers.py, COUNTRY_STYLE, on the
  // chips as data-slot and data-dash), the same whatever order it is picked in. Rankings flagged `pick`
  // colour the same countries and grey the others. The choice is remembered in this browser.
  var picker = document.getElementById("country-picker");
  var picked = [], pickStyle = {}, pickCodes = { Spain: "es" };
  var CSS_DASH = { solid: "solid", dash: "dashed", dot: "dotted" };

  function savePicks() {
    try { localStorage.setItem("ep-peers", JSON.stringify(picked)); } catch (e) { /* storage blocked: lasts this visit */ }
  }

  function togglePick(code) {
    var at = picked.indexOf(code);
    if (at >= 0) picked.splice(at, 1);
    else if (pickStyle[code]) picked.push(code);
  }

  function renderChips() {
    Array.prototype.forEach.call(document.querySelectorAll(".picker-chips .chip[data-country]"), function (b) {
      var code = b.getAttribute("data-country"), on = picked.indexOf(code) >= 0;
      b.setAttribute("aria-pressed", String(on));
      var swatch = b.querySelector(".chip-swatch");
      if (swatch) {   // a short stroke in the country's colour and line style; follows the theme
        swatch.style.borderTopColor = on ? "var(--series-" + pickStyle[code].slot + ")" : "";
        swatch.style.borderTopStyle = CSS_DASH[pickStyle[code].dash] || "solid";
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll(".bar-countries-count"), function (n) {
      n.textContent = String(picked.length);
    });
  }

  if (picker) {
    Array.prototype.forEach.call(picker.querySelectorAll(".chip[data-country]"), function (b) {
      var code = b.getAttribute("data-country");
      pickCodes[b.textContent.trim()] = code;
      pickStyle[code] = { slot: +b.getAttribute("data-slot") || 1, dash: b.getAttribute("data-dash") || "solid" };
    });
    var savedPicks = null;
    try { savedPicks = JSON.parse(localStorage.getItem("ep-peers") || "null"); } catch (e) { /* no saved choice */ }
    (Array.isArray(savedPicks) ? savedPicks : (picker.getAttribute("data-default") || "").split(",")).forEach(function (c) {
      if (picker.querySelector('.chip[data-country="' + c + '"]') && picked.indexOf(c) < 0) togglePick(c);
    });
    renderChips();
  }

  function seriesCountries(s) { return s.countries || (s.country ? [s.country] : []); }

  // The series a `pick` chart shows: Spain's (in ink) and the chosen countries' (in their colours). Where none
  // of the chosen countries has a series (the spreads, for euro-area countries only), the chart's own
  // defaults are drawn in grey.
  function pickView(spec) {
    if (!picker) return spec;
    var isSpain = function (s) { return seriesCountries(s).indexOf("es") >= 0; };
    var chosen = function (s) { return seriesCountries(s).filter(function (c) { return picked.indexOf(c) >= 0; })[0]; };
    var series = spec.series.filter(function (s) { return isSpain(s) || chosen(s); }).map(function (s) {
      return Object.assign({}, s, isSpain(s) ? { color: "ink" } : { slot: pickStyle[chosen(s)].slot, dash: pickStyle[chosen(s)].dash });
    });
    if (series.every(isSpain) && spec.pick_default) {
      series = series.concat(spec.series.filter(function (s) {
        return !isSpain(s) && seriesCountries(s).some(function (c) { return spec.pick_default.indexOf(c) >= 0; });
      }).map(function (s) { return Object.assign({}, s, { color: "muted" }); }));
    }
    var rank = function (s) { return isSpain(s) ? -1 : picked.indexOf(chosen(s)) >= 0 ? picked.indexOf(chosen(s)) : 9; };
    series.sort(function (a, b) { return rank(a) - rank(b); });
    return Object.assign({}, spec, { series: series });
  }

  function token(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // "%" and "k" attach to the number; other units ("pp", "€/MWh") follow after a space.
  function suffix(spec) {
    var u = spec.unit || "";
    return u === "%" || u === "k" ? u : (u ? " " + u : "");
  }

  function fmt(v, spec, signed) {
    var s = Math.abs(v).toLocaleString("en-GB", { minimumFractionDigits: spec.decimals, maximumFractionDigits: spec.decimals });
    var sign = v < 0 ? "−" : (signed && v > 0 ? "+" : "");
    return sign + s + suffix(spec);
  }

  function dateLabel(iso, freq) {
    var y = iso.slice(0, 4), m = parseInt(iso.slice(5, 7), 10);
    if (freq === "Q") return "Q" + (Math.floor((m - 1) / 3) + 1) + " " + y;
    if (freq === "D") return parseInt(iso.slice(8, 10), 10) + " " + MONTHS[m - 1] + " " + y;
    if (freq === "A") return y;
    return MONTHS[m - 1] + " " + y;
  }

  function hoverDate(spec) {
    if (spec.date_format) return spec.date_format;
    return spec.freq === "Q" ? "Q%q %Y" : spec.freq === "D" ? "%-d %b %Y" : spec.freq === "A" ? "%Y" : "%b %Y";
  }

  // Spanish month and day names on the charts' axes and in their hover labels; numbers keep the English format.
  if (LANG === "es" && window.Plotly && window.Plotly.register) {
    window.Plotly.register({ moduleType: "locale", name: "es", dictionary: {}, format: {
      days: ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
      shortDays: ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
      months: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
               "noviembre", "diciembre"],
      shortMonths: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
      date: "%d/%m/%Y", decimal: ".", thousands: "," } });
  }
  var CONFIG_BASE = {
    locale: LANG,
    displaylogo: false, responsive: true,
    modeBarButtonsToRemove: ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d",
      "resetScale2d", "toggleSpikelines", "hoverClosestCartesian", "hoverCompareCartesian"]
  };

  // Horizontal bars ranking regions or countries on one measure, largest first. One
  // colour (Spain, when listed among its peers, in text ink); a dotted reference line.
  function drawRanking(el, spec) {
    var s = spec.series[0];
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis");
    el.style.height = Math.max(220, s.x.length * 22 + 41 + Math.max(1, (spec.ref_lines || []).length) * 15) + "px";
    var format = ":." + spec.decimals + "f}" + suffix(spec);
    var traces = [{
      type: "bar", orientation: "h", x: s.y, y: s.x, showlegend: false,
      marker: { color: s.x.map(function (label) {
        if (label === spec.highlight) return ink;
        if (!spec.pick || !picker) return token("--series-1");
        var code = pickCodes[label];
        return picked.indexOf(code) >= 0 ? token("--series-" + pickStyle[code].slot) : token("--axis");
      }) },
      hovertemplate: "<b>%{x" + format + "</b>  %{y}<extra></extra>"
    }];
    var shapes = [], annotations = [];
    (spec.ref_lines || []).forEach(function (r, i) {
      shapes.push({ type: "line", yref: "paper", y0: 0, y1: 1, x0: r.y, x1: r.y, line: { color: ink2, width: 1, dash: r.dash || "dot" } });
      annotations.push({ x: r.y, xref: "x", y: 1, yref: "paper", yanchor: "bottom", yshift: i * 15, showarrow: false,
        text: r.label + " " + fmt(r.y, spec), font: { size: 11, color: ink2 } });
    });
    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 10, r: 18, t: annotations.length ? 9 + annotations.length * 15 : 8, b: 30 },
      hovermode: "closest", hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      yaxis: { type: "category", autorange: "reversed", automargin: true, fixedrange: true, ticks: "",
        tickfont: { color: ink2, size: 12 } },
      xaxis: { gridcolor: grid, zeroline: true, zerolinecolor: axis, fixedrange: true, tickfont: { color: muted },
        ticksuffix: suffix(spec), automargin: true },
      bargap: 0.3, barcornerradius: 3, shapes: shapes, annotations: annotations
    };
    var config = Object.assign({ toImageButtonOptions: { filename: "macroscope-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config);
  }

  // One measure against another over time (a Beveridge curve): a path of dated points,
  // the first and latest labelled.
  function drawXY(el, spec) {
    var s = spec.series[0], n = s.x.length;
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis"), color = token("--series-1");
    var unit = function (u) { return u === "%" || u === "k" ? u : (u ? " " + u : ""); };
    var hover = "<b>%{text}</b><br>" + spec.x_label + " %{x:.1f}" + unit(spec.x_unit) + "<br>" +
      spec.y_label + " %{y:.0f}" + unit(spec.y_unit) + "<extra></extra>";
    var traces = [
      { type: "scatter", mode: "lines+markers", x: s.x, y: s.y, text: s.text, hovertemplate: hover, showlegend: false,
        line: { color: color, width: 1.5 }, marker: { size: 6, color: color, line: { width: 1, color: surface } } },
      { type: "scatter", mode: "markers", x: [s.x[n - 1]], y: [s.y[n - 1]], hoverinfo: "skip", showlegend: false,
        marker: { size: 11, color: color, line: { width: 2, color: surface } } }
    ];
    var label = function (i, anchor) {
      return { x: s.x[i], y: s.y[i], text: s.text[i], showarrow: false, xanchor: anchor, xshift: anchor === "left" ? 9 : -9,
        font: { size: 11, color: ink2 } };
    };
    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 56, r: 18, t: 10, b: 44 }, hovermode: "closest", showlegend: false,
      hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      xaxis: { title: { text: spec.x_label + (spec.x_unit ? " (" + spec.x_unit + ")" : ""), font: { size: 12, color: ink2 } },
        gridcolor: grid, zeroline: false, linecolor: axis, fixedrange: true, tickfont: { color: muted } },
      yaxis: { title: { text: spec.y_label + (spec.y_unit ? " (" + spec.y_unit + ")" : ""), font: { size: 12, color: ink2 } },
        gridcolor: grid, zeroline: false, fixedrange: true, tickfont: { color: muted }, automargin: true },
      annotations: [label(0, "right"), label(n - 1, "left")]
    };
    var config = Object.assign({ toImageButtonOptions: { filename: "macroscope-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config);
  }

  // A dot plot, one row per person (the ECB-speak standings): a heavy dot for the current
  // stance, small numbered dots for the latest readings (1 = most recent) and a band for the range.
  function drawDots(el, spec) {
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis");
    var blue = token("--series-1"), orange = token("--series-2");
    var rows = spec.rows;
    el.style.height = Math.max(220, rows.length * 30 + 70) + "px";
    var labels = rows.map(function (r) { return r.label; });
    var band = { x: [], y: [] }, recent = { x: [], y: [], text: [] };
    rows.forEach(function (r) {
      if (r.range) { band.x.push(r.range[0], r.range[1], null); band.y.push(r.label, r.label, null); }
      (r.recent || []).forEach(function (v, i) {
        if (v === null || v === undefined) return;
        recent.x.push(v); recent.y.push(r.label); recent.text.push(String(i + 1));
      });
    });
    var traces = [
      { type: "scatter", mode: "lines", x: band.x, y: band.y, hoverinfo: "skip", showlegend: false,
        line: { color: axis, width: 7 }, opacity: 0.6 },
      { type: "scatter", mode: "markers+text", x: recent.x, y: recent.y, text: recent.text, textposition: "top center",
        textfont: { size: 9, color: ink2 }, showlegend: false, marker: { size: 8, color: surface, line: { color: ink2, width: 1.5 } },
        hovertemplate: t("Reading") + " %{text}: <b>%{x:+." + spec.decimals + "f}</b><extra>%{y}</extra>" },
      { type: "scatter", mode: "markers", x: rows.map(function (r) { return r.stance; }), y: labels, showlegend: false,
        marker: { size: 13, color: rows.map(function (r) { return r.highlight ? orange : blue; }), line: { color: surface, width: 2 } },
        customdata: rows.map(function (r) { return r.sub || ""; }),
        hovertemplate: "<b>%{x:+." + spec.decimals + "f}</b> %{y}<br>%{customdata}<extra></extra>" }
    ];
    var lo = spec.x_range[0], hi = spec.x_range[1];
    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 10, r: 18, t: 8, b: 44 },
      hovermode: "closest", hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      yaxis: { type: "category", categoryorder: "array", categoryarray: labels, autorange: "reversed", automargin: true,
        fixedrange: true, ticks: "", tickfont: { color: ink2, size: 12 } },
      xaxis: { range: [lo, hi], gridcolor: grid, zeroline: true, zerolinecolor: ink2, zerolinewidth: 1, fixedrange: true,
        tickfont: { color: muted }, tickformat: "+d" },
      annotations: [
        { x: lo, xref: "x", y: 0, yref: "paper", yshift: -32, xanchor: "left", showarrow: false, text: "← " + (spec.left || "lower"), font: { size: 11, color: ink2 } },
        { x: hi, xref: "x", y: 0, yref: "paper", yshift: -32, xanchor: "right", showarrow: false, text: (spec.right || "higher") + " →", font: { size: 11, color: ink2 } }
      ]
    };
    var config = Object.assign({ toImageButtonOptions: { filename: "macroscope-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config);
  }

  // The same items in two years: a hollow dot for the earlier year, a filled one for the later, joined by a
  // thin bar, one row per item in the order given (a highlighted row's dot in text ink). The hover gives the
  // row's note (its change).
  function drawDumbbell(el, spec) {
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis"), blue = token("--series-1");
    var rows = spec.rows;
    el.style.height = Math.max(220, rows.length * 26 + 76) + "px";
    var labels = rows.map(function (r) { return r.label; });
    var link = { x: [], y: [] };
    rows.forEach(function (r) {
      if (r.a === null || r.a === undefined || r.b === null || r.b === undefined) return;
      link.x.push(r.a, r.b, null); link.y.push(r.label, r.label, null);
    });
    var format = ":." + spec.decimals + "f}" + suffix(spec);
    var traces = [
      { type: "scatter", mode: "lines", x: link.x, y: link.y, hoverinfo: "skip", showlegend: false,
        line: { color: axis, width: 3 } },
      { type: "scatter", mode: "markers", name: spec.a_name, x: rows.map(function (r) { return r.a; }), y: labels,
        marker: { size: 10, color: surface, line: { color: ink2, width: 2 } },
        hovertemplate: "<b>%{x" + format + "</b>  " + spec.a_name + "<extra>%{y}</extra>" },
      { type: "scatter", mode: "markers", name: spec.b_name, x: rows.map(function (r) { return r.b; }), y: labels,
        marker: { size: 11, color: rows.map(function (r) { return r.highlight ? ink : blue; }), line: { color: surface, width: 2 } },
        customdata: rows.map(function (r) { return r.note || ""; }),
        hovertemplate: "<b>%{x" + format + "</b>  " + spec.b_name + "<br>%{customdata}<extra>%{y}</extra>" }
    ];
    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 10, r: 18, t: 30, b: 30 }, showlegend: true,
      legend: { orientation: "h", x: 0, xanchor: "left", y: 1.0, yanchor: "bottom", font: { size: 12, color: ink2 } },
      hovermode: "closest", hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      yaxis: { type: "category", categoryorder: "array", categoryarray: labels, autorange: "reversed", automargin: true,
        fixedrange: true, ticks: "", tickfont: { color: ink2, size: 12 } },
      xaxis: { gridcolor: grid, zeroline: true, zerolinecolor: axis, fixedrange: true, tickfont: { color: muted },
        ticksuffix: suffix(spec), automargin: true }
    };
    var config = Object.assign({ toImageButtonOptions: { filename: "macroscope-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config);
  }

  function draw(spec) {
    var el = document.getElementById("chart-" + spec.id);
    if (!el || !window.Plotly) return;
    if (spec.kind === "hbar") return drawRanking(el, spec);
    if (spec.kind === "dumbbell") return drawDumbbell(el, spec);
    if (spec.kind === "dots") return drawDots(el, spec);
    if (spec.kind === "xy") return drawXY(el, spec);
    if (spec.pick) spec = pickView(spec);
    // Fixed slot order, never cycled: a spec has at most six palette series (slots 4 to 6 come dashed, as some
    // of their colours sit close to the first three's). Slot 7 (violet) serves only a picked country's line.
    var colors = [1, 2, 3, 4, 5, 6, 7].map(function (n) { return token("--series-" + n); });
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis");
    var multi = spec.series.length > 1;
    // Curves (yields by maturity, rates by horizon) have a category axis instead of dates.
    var category = spec.x_kind === "category";
    // On narrow (phone-width) charts the legend names the lines; end labels would squeeze the plot.
    // With many lines (every comparator picked) the end labels would pile up: the legend names them instead.
    var endLabels = multi && el.clientWidth >= 480 && spec.series.length <= 6;
    var valueFormat = ":" + (spec.signed ? "+" : "") + "." + spec.decimals + "f}" + suffix(spec);

    // Dense bar charts (monthly bars over many years) drop the gaps and rounding, which would read as stripes.
    var dense = spec.series[0].x.length > 60;
    var traces = [];
    var annotations = [];
    var slot = 0;
    spec.series.forEach(function (s) {
      // A total drawn in text colour takes no palette slot; a series can share a slot (a fan chart's bounds).
      var color = s.color === "ink" ? ink : s.color === "muted" ? muted : s.slot ? colors[s.slot - 1] : colors[slot++];
      var kind = s.kind || spec.kind;
      // Value leads, name follows; the colored key comes from Plotly's swatch.
      var template = "<b>%{y" + valueFormat + "</b>  " + s.name + "<extra></extra>";
      if (kind === "bar") {
        traces.push({
          type: "bar", x: s.x, y: s.y, name: s.name, hovertemplate: template,
          // Stacked segments are separated by a thin gap in the surface colour.
          marker: { color: color, line: { color: surface, width: spec.stack && !dense ? 1.5 : 0 } }
        });
        return;
      }
      traces.push({
        type: "scatter", mode: category ? "lines+markers" : "lines", x: s.x, y: s.y, name: s.name,
        line: { color: color, width: 2, shape: s.shape || "linear", dash: s.dash || "solid" }, hovertemplate: template,
        // A curve has few points: mark each one (with a surface ring), as on a line with sparse data.
        marker: { size: 7, color: color, line: { width: 1.5, color: surface } }
      });
      // End dot with a surface ring, and a direct label in text ink.
      var lastX = s.x[s.x.length - 1], lastY = s.y[s.y.length - 1];
      traces.push({
        type: "scatter", mode: "markers", x: [lastX], y: [lastY], showlegend: false, hoverinfo: "skip",
        marker: { size: 9, color: color, line: { width: 2, color: surface } }
      });
      if (endLabels) {
        // In the right margin (paper x = 1), so the label doesn't stretch the date axis.
        annotations.push({
          x: 1, xref: "paper", y: lastY, yref: "y", text: s.name + " " + fmt(lastY, spec, spec.signed),
          showarrow: false, xanchor: "left", xshift: 8, font: { size: 12, color: ink2 }
        });
      }
    });

    var shapes = (spec.ref_lines || []).map(function (r) {
      // Labelled in the right margin with the series end labels, clear of the lines.
      annotations.push({
        x: 1, xref: "paper", y: r.y, yref: "y", text: r.label, showarrow: false,
        xanchor: "left", xshift: 8, font: { size: 11, color: ink2 }
      });
      return { type: "line", xref: "paper", x0: 0, x1: 1, y0: r.y, y1: r.y, line: { color: axis, width: 1 } };
    });
    // Shapes don't count towards the axis range: an invisible point keeps each reference line in view.
    (spec.ref_lines || []).forEach(function (r) {
      traces.push({ type: "scatter", mode: "markers", x: [spec.series[0].x[0]], y: [r.y], marker: { opacity: 0 },
        hoverinfo: "skip", showlegend: false });
    });

    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 44, r: labelMargin(annotations), t: multi ? 30 : 10, b: 30 },
      showlegend: multi,
      legend: { orientation: "h", x: 0, xanchor: "left", y: 1.02, yanchor: "bottom", font: { size: 12, color: ink2 } },
      hovermode: "x unified",
      hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      xaxis: category ? {
        type: "category", showgrid: false, showline: true, linecolor: axis, ticks: "", fixedrange: true,
        tickfont: { color: muted }, showspikes: true, spikemode: "across", spikethickness: 1,
        spikecolor: axis, spikedash: "solid"
      } : {
        type: "date", showgrid: false, showline: true, linecolor: axis, ticks: "", fixedrange: true,
        hoverformat: hoverDate(spec),
        tickfont: { color: muted }, showspikes: true, spikemode: "across", spikethickness: 1,
        spikecolor: axis, spikedash: "solid", spikesnap: "cursor"
      },
      yaxis: {
        // The zero line shows whenever zero is in range (growth rates, monthly changes).
        gridcolor: grid, gridwidth: 1, zeroline: true, zerolinecolor: axis, zerolinewidth: 1,
        fixedrange: true, tickfont: { color: muted }, ticksuffix: suffix(spec), automargin: true
      },
      barmode: spec.stack ? "relative" : "group",
      bargap: dense ? 0 : 0.3, barcornerradius: dense ? 0 : 4,
      annotations: annotations, shapes: shapes
    };
    // A chosen time window (5 or 10 years...) narrows the date axis and fits the vertical axis to it.
    var win = category ? null : rangeWindow(spec);
    if (win) {
      layout.xaxis.range = win.x;
      layout.yaxis.range = win.y;
    } else {
      layout.xaxis.autorange = true;
      layout.yaxis.autorange = true;
    }
    var config = Object.assign({ toImageButtonOptions: { filename: "macroscope-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config).then(function () { spreadLabels(el); });
  }

  // ---------------------------------------------------------------- time ranges
  // Long time series get buttons for the last few years. The choice is kept per chart for the visit and
  // survives redraws (theme, resize, a tool's new settings).
  var ranges = {};
  var DAY = 86400000;

  function isoDate(t) { return new Date(t).toISOString().slice(0, 10); }
  function parseIso(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10) || 1); }
  function yearsBack(s, years) { return isoDate(Date.UTC(+s.slice(0, 4) - years, +s.slice(5, 7) - 1, +s.slice(8, 10) || 1)); }

  function dateSpan(spec) {
    var first = null, last = null;
    spec.series.forEach(function (s) {
      if (!s.x.length) return;
      if (first === null || s.x[0] < first) first = s.x[0];
      if (last === null || s.x[s.x.length - 1] > last) last = s.x[s.x.length - 1];
    });
    return first === null ? null : { first: first, last: last, years: (parseIso(last) - parseIso(first)) / (365.25 * DAY) };
  }

  // The windows worth offering: a window must be clearly shorter than the data. Annual charts are short,
  // and often end in projections, so they keep their whole span.
  function rangeOptions(spec) {
    if (spec.x_kind === "category" || ["hbar", "xy", "dots", "dumbbell"].indexOf(spec.kind) >= 0 || spec.freq === "A" ||
        !spec.series || !spec.series.length) return [];
    var span = dateSpan(spec);
    if (!span) return [];
    return (spec.freq === "D" ? [1, 5] : [5, 10]).filter(function (y) { return span.years > y * 1.25; });
  }

  function rangeWindow(spec) {
    var years = ranges[spec.id];
    var span = years && dateSpan(spec);
    if (!span) return null;
    var cutoff = yearsBack(span.last, years);
    var lo = Infinity, hi = -Infinity, first = null, bars = false, up = {}, down = {};
    spec.series.forEach(function (s) {
      var bar = (s.kind || spec.kind) === "bar";
      s.x.forEach(function (x, i) {
        var v = s.y[i];
        if (x <= cutoff || v === null || v === undefined) return;
        if (first === null || x < first) first = x;
        if (bar) {
          bars = true;
          if (spec.stack) {   // stacked bars: the visible range is set by each date's positive and negative totals
            if (v >= 0) up[x] = (up[x] || 0) + v; else down[x] = (down[x] || 0) + v;
            return;
          }
        }
        lo = Math.min(lo, v); hi = Math.max(hi, v);
      });
    });
    Object.keys(up).forEach(function (k) { hi = Math.max(hi, up[k]); lo = Math.min(lo, 0); });
    Object.keys(down).forEach(function (k) { lo = Math.min(lo, down[k]); hi = Math.max(hi, 0); });
    if (bars) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    if (!isFinite(lo) || first === null) return null;
    var pad = (hi - lo) * 0.06 || Math.abs(hi) * 0.1 || 1;
    // Room at the edges: half a period for bars, and enough for the end dots of lines.
    var start = parseIso(first), end = parseIso(span.last);
    var room = Math.max(bars ? ({ D: 1, M: 16, Q: 46, A: 183 }[spec.freq] || 16) * DAY : 0, (end - start) * 0.015);
    return {
      x: [isoDate(start - room), isoDate(end + room)],
      y: [bars && lo === 0 ? 0 : lo - pad, bars && hi === 0 ? 0 : hi + pad]
    };
  }

  function addRangeButtons(spec) {
    var fig = document.getElementById("fig-" + spec.id), options = rangeOptions(spec);
    if (!fig || !options.length || fig.querySelector(".range-buttons")) return;
    var caption = fig.querySelector("figcaption");
    if (!caption) return;
    var group = document.createElement("div");
    group.className = "range-buttons";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", t("Time range"));
    options.concat([0]).forEach(function (years) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = years ? years + (LANG === "es" ? "A" : "Y") : t("All");
      b.setAttribute("data-years", years);
      b.setAttribute("aria-label", years ? (LANG === "es" ? "Últimos " + years + (years === 1 ? " año" : " años")
                                                         : "Last " + years + (years === 1 ? " year" : " years")) : t("All the data"));
      b.setAttribute("aria-pressed", String((ranges[spec.id] || 0) === years));
      group.appendChild(b);
    });
    caption.classList.add("has-range");
    caption.appendChild(group);
  }

  document.addEventListener("click", function (event) {
    var b = event.target.closest && event.target.closest(".range-buttons button");
    if (!b) return;
    var fig = b.closest(".chart-card"), spec = fig && byId(fig.id.slice("fig-".length));
    if (!spec) return;
    ranges[spec.id] = +b.getAttribute("data-years") || null;
    Array.prototype.forEach.call(b.parentNode.querySelectorAll("button"), function (other) {
      other.setAttribute("aria-pressed", String(other === b));
    });
    drawSpec(spec);
  });

  // Right margin wide enough for the longest end label (about 6.5px a character at 12px).
  function labelMargin(annotations) {
    var longest = 0;
    annotations.forEach(function (a) { longest = Math.max(longest, a.text.length); });
    return longest ? Math.min(180, Math.round(longest * 6.5) + 18) : 14;
  }

  // End labels of lines that finish close together would overlap: push them apart
  // vertically (at least 15px) once Plotly has laid out the axis.
  function spreadLabels(el) {
    try {
      var ya = el._fullLayout.yaxis, height = el._fullLayout._size.h;
      var notes = el.layout.annotations || [];
      if (notes.length < 2) return;
      var items = notes.map(function (a, i) { return { i: i, px: ya.l2p(a.y), orig: ya.l2p(a.y) }; });
      items.sort(function (a, b) { return a.px - b.px; });
      for (var k = 1; k < items.length; k++) {
        if (items[k].px - items[k - 1].px < 15) items[k].px = items[k - 1].px + 15;
      }
      var overflow = items[items.length - 1].px - height;
      var update = {};
      items.forEach(function (it) {
        var px = overflow > 0 ? it.px - overflow : it.px;
        update["annotations[" + it.i + "].yshift"] = it.orig - px;  // yshift is upwards
      });
      window.Plotly.relayout(el, update);
    } catch (e) { /* labels stay where they are */ }
  }

  // A plain table under each chart, so every value is readable without hovering. Time series show
  // their latest 12 dates, or every date once asked (`all`).
  function fillTable(spec, all) {
    var holder = document.querySelector('.chart-data[data-chart="' + spec.id + '"]');
    if (!holder) return;
    if (all === undefined && holder.querySelector("table")) return;
    if (spec.pick) spec = pickView(spec);
    Array.prototype.forEach.call(holder.querySelectorAll("table, .note"), function (el) { holder.removeChild(el); });
    var table = document.createElement("table");
    var category = spec.x_kind === "category";
    var head = table.createTHead().insertRow();
    if (spec.kind === "xy") return fillXYTable(spec, holder, table, head);
    if (spec.kind === "dumbbell") {
      [spec.x_title || t("Item"), spec.a_name, spec.b_name, t("Change")].forEach(function (h) {
        var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
      });
      var rb = table.createTBody();
      spec.rows.forEach(function (r) {
        var tr = rb.insertRow();
        tr.insertCell().textContent = r.label;
        tr.insertCell().textContent = r.a === null || r.a === undefined ? "–" : fmt(r.a, spec);
        tr.insertCell().textContent = r.b === null || r.b === undefined ? "–" : fmt(r.b, spec);
        tr.insertCell().textContent = r.note || "–";
      });
      holder.appendChild(table);
      return;
    }
    if (spec.kind === "dots") {
      ["Member", "Stance", "Latest", "Range over the year"].map(t).forEach(function (h) {
        var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
      });
      var tb = table.createTBody();
      spec.rows.forEach(function (r) {
        var tr = tb.insertRow();
        tr.insertCell().textContent = r.label;
        tr.insertCell().textContent = fmt(r.stance, spec, true);
        tr.insertCell().textContent = (r.recent || []).filter(function (v) { return v !== null; }).map(function (v) { return fmt(v, spec, true); }).join(", ");
        tr.insertCell().textContent = r.range ? fmt(r.range[0], spec, true) + t(" to ") + fmt(r.range[1], spec, true) : "–";
      });
      holder.appendChild(table);
      return;
    }
    [spec.x_title || t("Date")].concat(spec.series.map(function (s) { return s.name; })).forEach(function (h) {
      var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
    });
    // Curves: every point in order. Time series: every date any series has (they can
    // differ in frequency), newest first.
    var seen = {}, dates = [];
    spec.series.forEach(function (s) {
      s.x.forEach(function (d) { if (!seen[d]) { seen[d] = true; dates.push(d); } });
    });
    var total = dates.length;
    if (!category) dates = dates.sort().reverse().slice(0, all ? total : 12);
    var maps = spec.series.map(function (s) {
      var m = {};
      s.x.forEach(function (x, i) { m[x] = s.y[i]; });
      return m;
    });
    var body = table.createTBody();
    dates.forEach(function (d) {
      var row = body.insertRow();
      row.insertCell().textContent = category ? d : dateLabel(d, spec.freq);
      maps.forEach(function (m) {
        row.insertCell().textContent = d in m && m[d] !== null ? fmt(m[d], spec, spec.signed) : "–";
      });
    });
    var caption = document.createElement("p");
    caption.className = "note";
    if (category || total <= 12) {
      caption.textContent = category ? t("All points.") : (LANG === "es" ? "Las " + total + " fechas." : "All " + total + " dates.");
    } else {
      caption.textContent = LANG === "es"
        ? (all ? "Las " + total + " fechas, de la más reciente a la más antigua. " : "Las últimas 12 de " + total + " fechas. ")
        : (all ? "All " + total + " dates, newest first. " : "Latest 12 of " + total + " dates. ");
      var more = document.createElement("button");
      more.type = "button";
      more.className = "chart-link table-all";
      more.textContent = LANG === "es" ? (all ? "Ver las últimas 12" : "Ver las " + total)
                                       : (all ? "Show the latest 12" : "Show all " + total);
      more.addEventListener("click", function () { fillTable(spec, !all); });
      caption.appendChild(more);
    }
    holder.appendChild(table);
    holder.appendChild(caption);
  }

  function fillXYTable(spec, holder, table, head) {
    [spec.x_title, spec.x_label, spec.y_label].forEach(function (h) {
      var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
    });
    var s = spec.series[0], body = table.createTBody();
    for (var i = s.x.length - 1; i >= Math.max(0, s.x.length - 12); i--) {
      var row = body.insertRow();
      row.insertCell().textContent = s.text[i];
      row.insertCell().textContent = s.x[i].toFixed(1) + (spec.x_unit === "%" ? "%" : "");
      row.insertCell().textContent = s.y[i].toFixed(0) + (spec.y_unit === "k" ? "k" : "");
    }
    var caption = document.createElement("p");
    caption.className = "note";
    caption.textContent = t("Latest 12 periods.");
    holder.appendChild(table);
    holder.appendChild(caption);
  }

  document.addEventListener("click", function (event) {
    var chip = event.target.closest && event.target.closest(".picker-chips .chip");
    if (!chip || !picker) return;
    var all = chip.getAttribute("data-pick");
    if (all === "all") picked = Object.keys(pickStyle);
    else if (all === "none") picked = [];
    else togglePick(chip.getAttribute("data-country"));
    savePicks();
    renderChips();
    drawAll();
    Array.prototype.forEach.call(document.querySelectorAll(".chart-data[open]"), function (holder) {
      var spec = byId(holder.getAttribute("data-chart"));
      if (spec && spec.pick) fillTable(spec, false);
    });
  });

  // ---------------------------------------------------------------- drawing as charts come into view
  // A page can carry 30 charts or more: each is drawn when it nears the screen, and a theme switch or
  // a resize redraws only those already drawn. Rankings and dot plots get their height first, so
  // drawing them later doesn't move the page.
  var drawn = {};

  function byId(id) {
    for (var i = 0; i < specs.length; i++) if (specs[i].id === id) return specs[i];
    return null;
  }

  function presize(spec) {
    var el = document.getElementById("chart-" + spec.id);
    if (!el) return;
    if (spec.kind === "hbar") el.style.height = Math.max(220, spec.series[0].x.length * 22 + 41 + Math.max(1, (spec.ref_lines || []).length) * 15) + "px";
    if (spec.kind === "dumbbell") el.style.height = Math.max(220, spec.rows.length * 26 + 76) + "px";
    if (spec.kind === "dots") el.style.height = Math.max(220, spec.rows.length * 30 + 70) + "px";
  }

  function drawSpec(spec) {
    drawn[spec.id] = true;
    draw(spec);
  }

  function drawAll() {
    specs.forEach(function (s) { if (drawn[s.id]) draw(s); });
  }

  function drawEverything() {
    specs.forEach(function (s) { if (!drawn[s.id]) drawSpec(s); });
  }

  var observer = "IntersectionObserver" in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      var spec = byId(entry.target.id.slice("chart-".length));
      if (spec) drawSpec(spec);
    });
  }, { rootMargin: "400px 0px" }) : null;

  // ---------------------------------------------------------------- CSV download
  // Every value a chart carries (not just what the data table shows), one row per date or item.
  function csvCell(v) {
    var s = v === null || v === undefined ? "" : String(v);
    return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function csvRows(spec) {
    var unit = spec.unit ? " (" + spec.unit + ")" : "";
    if (spec.kind === "hbar") {
      var bars = spec.series[0];
      return [[spec.x_title || t("Item"), bars.name + unit]].concat(bars.x.map(function (x, i) { return [x, bars.y[i]]; }));
    }
    if (spec.kind === "xy") {
      var path = spec.series[0];
      return [[spec.x_title || t("Period"), spec.x_label, spec.y_label]].concat(
        path.x.map(function (x, i) { return [path.text[i], x, path.y[i]]; }));
    }
    if (spec.kind === "dumbbell") {
      return [[spec.x_title || t("Item"), spec.a_name + unit, spec.b_name + unit]].concat(spec.rows.map(function (r) { return [r.label, r.a, r.b]; }));
    }
    if (spec.kind === "dots") {
      return [["Member", "Stance", "Lowest over the year", "Highest over the year"].map(t)].concat(spec.rows.map(function (r) {
        return [r.label, r.stance, r.range ? r.range[0] : "", r.range ? r.range[1] : ""];
      }));
    }
    var keys = [], seen = {}, maps = spec.series.map(function (s) {
      var m = {};
      s.x.forEach(function (x, i) { m[x] = s.y[i]; if (!seen[x]) { seen[x] = true; keys.push(x); } });
      return m;
    });
    if (spec.x_kind !== "category") keys.sort();
    return [[spec.x_title || t("Date")].concat(spec.series.map(function (s) { return s.name + unit; }))].concat(
      keys.map(function (k) { return [k].concat(maps.map(function (m) { return k in m ? m[k] : ""; })); }));
  }

  function downloadCsv(spec) {
    // A byte-order mark so spreadsheet programs read "€" and accents correctly.
    var text = "﻿" + csvRows(spec).map(function (r) { return r.map(csvCell).join(","); }).join("\r\n") + "\r\n";
    var url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
    var a = document.createElement("a");
    a.href = url; a.download = "macroscope-" + spec.id + ".csv";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // ---------------------------------------------------------------- chart links
  // "Copy link" puts this page's address with the chart's anchor (#fig-<id>) on the clipboard.
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var area = document.createElement("textarea");
      area.value = text; area.setAttribute("readonly", ""); area.style.position = "fixed"; area.style.opacity = "0";
      document.body.appendChild(area); area.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (e) { reject(e); }
      document.body.removeChild(area);
    });
  }
  document.addEventListener("click", function (event) {
    var csv = event.target.closest && event.target.closest(".chart-csv");
    if (csv) {
      var spec = byId(csv.getAttribute("data-chart"));
      if (spec) downloadCsv(spec);
      return;
    }
    var button = event.target.closest && event.target.closest(".chart-link[data-figure]");
    if (!button) return;
    var url = location.href.split(/[?#]/)[0] + "#" + button.getAttribute("data-figure");
    var label = button.textContent;
    function show(text) {
      button.textContent = text;
      setTimeout(function () { button.textContent = label; }, 2000);
    }
    copyText(url).then(function () { show(t("Link copied")); }, function () { window.prompt(t("Copy this link:"), url); });
  });

  // A chart's data table is filled the first time it is opened.
  document.addEventListener("toggle", function (event) {
    var holder = event.target;
    if (!holder.classList || !holder.classList.contains("chart-data") || !holder.open) return;
    var spec = byId(holder.getAttribute("data-chart"));
    if (spec) fillTable(spec);
  }, true);

  // A chart with no data has nothing to download.
  function csvButton(id) { return document.querySelector('.chart-csv[data-chart="' + id + '"]'); }
  Array.prototype.forEach.call(document.querySelectorAll(".chart-csv"), function (b) {
    b.hidden = !byId(b.getAttribute("data-chart"));
  });

  specs.forEach(function (spec) {
    presize(spec);
    addRangeButtons(spec);
    var el = document.getElementById("chart-" + spec.id);
    if (!el) return;
    if (observer) observer.observe(el); else drawSpec(spec);
  });
  window.addEventListener("beforeprint", drawEverything);
  // Bring a linked chart (#fig-<id>) into view once the rankings above it have their height.
  if (location.hash.indexOf("#fig-") === 0) {
    var linked = document.getElementById(location.hash.slice(1));
    if (linked) linked.scrollIntoView();
  }

  // For pages that build charts in the browser (the tools): draw a spec now, and again
  // whenever the theme or the window size changes, like the charts written by the build.
  window.EP = window.EP || {};
  window.EP.render = function (spec) {
    var b = csvButton(spec.id);
    if (b) b.hidden = false;
    addRangeButtons(spec);
    for (var i = 0; i < specs.length; i++) {
      if (specs[i].id === spec.id) { specs[i] = spec; drawSpec(spec); return; }
    }
    specs.push(spec);
    drawSpec(spec);
  };
  window.EP.fmt = fmt;

  // ---------------------------------------------------------------- section links and back to top
  // A "#" after each section heading links to it (and copies the link).
  Array.prototype.forEach.call(document.querySelectorAll("main h2[id]"), function (h) {
    var a = document.createElement("a");
    a.className = "anchor";
    a.href = "#" + h.id;
    a.setAttribute("aria-label", t("Copy a link to the section") + " " + (h.firstChild ? h.firstChild.textContent : h.textContent).trim());
    a.textContent = "#";
    a.addEventListener("click", function (event) {
      event.preventDefault();
      history.replaceState(null, "", "#" + h.id);
      h.scrollIntoView();
      copyText(location.href).then(function () {
        a.classList.add("copied");
        setTimeout(function () { a.classList.remove("copied"); }, 1800);
      }, function () { /* the address bar has the link */ });
    });
    h.appendChild(a);
  });

  // ---------------------------------------------------------------- site search
  // The button (or "/" or Ctrl+K) opens a panel over the page. The index (data/search.js: every page,
  // section, chart and series) loads the first time; matching ignores case and accents, and every word
  // typed must appear in the title, the place or the Spanish name.
  (function () {
    var opener = document.getElementById("search-open"), panel = document.getElementById("search-panel");
    if (!opener || !panel) return;
    var input = document.getElementById("search-input"), list = document.getElementById("search-results");
    var hint = panel.querySelector(".search-hint");
    var KINDS = ["Page", "Section", "Chart", "Series"].map(t), BONUS = [5, 4, 2, 0];
    var index = null, loading = false, results = [], active = -1;

    function norm(s) { return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }

    function prepare() {
      index = (window.EP.search || []).map(function (e) {
        return { kind: e[0], title: e[1], context: e[2], href: e[3], t: norm(e[1]), all: norm(e[1] + " " + e[2] + " " + e[4]) };
      });
    }

    function load(then) {
      if (index) return then();
      if (window.EP && window.EP.search) { prepare(); return then(); }
      if (loading) return;
      loading = true;
      hint.textContent = t("Loading the index…");
      var script = document.createElement("script");
      script.src = opener.getAttribute("data-index");
      script.onload = function () { prepare(); then(); };
      script.onerror = function () { loading = false; hint.textContent = t("The search index could not be loaded."); };
      document.head.appendChild(script);
    }

    function wordStart(text, at) { return at === 0 || /[\s(,·/-]/.test(text.charAt(at - 1)); }

    function score(e, words, q) {
      var s = BONUS[e.kind] - e.title.length / 60;
      for (var i = 0; i < words.length; i++) {
        var at = e.all.indexOf(words[i]);
        if (at < 0) return -1;
        var inTitle = e.t.indexOf(words[i]);
        s += inTitle >= 0 ? (wordStart(e.t, inTitle) ? 6 : 3) : (wordStart(e.all, at) ? 2 : 1);
      }
      var whole = e.t.indexOf(q);
      return s + (whole === 0 ? 8 : whole > 0 ? 3 : 0);
    }

    function matches(words, q) {
      var found = [];
      index.forEach(function (e) { var s = score(e, words, q); if (s >= 0) found.push({ e: e, s: s }); });
      found.sort(function (a, b) { return b.s - a.s; });
      return found.slice(0, 20).map(function (f) { return f.e; });
    }

    function search() {
      var q = norm(input.value).trim();
      results = [];
      if (q) {
        var words = q.split(/\s+/);
        results = matches(words, q);
        // Nothing? Try the stems of the longer words ("electricidad" finds "eléctrica" and "electricity").
        if (!results.length && words.some(function (w) { return w.length >= 6; })) {
          results = matches(words.map(function (w) { return w.length >= 6 ? w.slice(0, Math.max(5, Math.ceil(w.length * 0.67))) : w; }), q);
        }
      }
      list.innerHTML = "";
      results.forEach(function (e, i) {
        var li = document.createElement("li"), a = document.createElement("a");
        li.id = "search-opt-" + i;
        li.setAttribute("role", "option");
        a.href = e.href;
        a.tabIndex = -1;
        var title = document.createElement("span"), where = document.createElement("span");
        title.className = "search-title"; title.textContent = e.title;
        where.className = "search-context"; where.textContent = KINDS[e.kind] + (e.kind ? " · " + e.context : "");
        a.appendChild(title); a.appendChild(where); li.appendChild(a); list.appendChild(li);
      });
      setActive(results.length ? 0 : -1);
      input.setAttribute("aria-expanded", String(results.length > 0));
      hint.textContent = LANG === "es"
        ? (!q ? "Todas las series, gráficos y secciones del sitio. Pruebe «paro», «precios de vivienda» o «exportaciones a China»."
              : results.length ? "" : "Nada coincide con «" + input.value.trim() + "».")
        : (!q ? "Every series, chart and section on the site. Try “paro”, “house prices” or “exports to China”."
              : results.length ? "" : "Nothing matches “" + input.value.trim() + "”.");
    }

    function setActive(i) {
      active = i;
      Array.prototype.forEach.call(list.children, function (li, k) { li.setAttribute("aria-selected", String(k === i)); });
      if (i >= 0) {
        input.setAttribute("aria-activedescendant", "search-opt-" + i);
        list.children[i].scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function show() {
      if (!panel.hidden) return input.focus();
      panel.hidden = false;
      document.body.classList.add("search-on");
      input.focus();
      input.select();
      load(search);
    }

    function hide(refocus) {
      panel.hidden = true;
      document.body.classList.remove("search-on");
      if (refocus) opener.focus();
    }

    opener.addEventListener("click", show);
    panel.addEventListener("click", function (e) {
      if (e.target === panel) hide(true);
      else if (e.target.closest("a")) hide(false);   // a result on this page only moves the page
    });
    input.addEventListener("input", function () { if (index) search(); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (results.length) setActive((active + (e.key === "ArrowDown" ? 1 : -1) + results.length) % results.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (active >= 0) { hide(false); location.href = results[active].href; }
      } else if (e.key === "Escape") {
        e.preventDefault();
        hide(true);
      } else if (e.key === "Tab") {
        e.preventDefault();                             // the input is the panel's only control
      }
    });
    document.addEventListener("keydown", function (e) {
      var el = document.activeElement, typing = el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);
      if ((e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) ||
          ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K"))) {
        e.preventDefault();
        show();
      }
    });
  })();

  // ---------------------------------------------------------------- where you are on a long page
  // Once the list of sections at the top scrolls away, a slim bar names the section you are reading;
  // it opens the list. The current section is also marked in the list at the top.
  (function () {
    var nav = document.querySelector("nav.on-page");
    if (!nav || document.querySelector(".sector-controls")) return;   // Sector tables keep their own sticky bar
    var links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]')).filter(function (a) {
      return document.getElementById(a.getAttribute("href").slice(1));
    });
    if (links.length < 3) return;
    var heads = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); });
    var bar = document.createElement("div");
    bar.className = "section-bar";
    bar.hidden = true;
    bar.innerHTML = '<div class="wrap section-bar-inner"><button type="button" class="section-bar-toggle" aria-expanded="false">' +
      '<span class="section-bar-label">' + t("On this page") + '</span><strong></strong><svg viewBox="0 0 10 6" width="10" height="6" ' +
      'aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>' +
      '<nav class="section-bar-menu" aria-label="' + t("Sections of this page") + '" hidden></nav></div>';
    var toggle = bar.querySelector("button"), current = bar.querySelector("strong"), menu = bar.querySelector("nav");
    // On a page with the country chooser, the bar also carries it: "Countries (n)", which opens every chip,
    // wrapped, none cut off (a row of chips ran off the edge before Batch 34a).
    var countries = null, countriesToggle = null, barChips = null;
    if (picker) {
      countries = document.createElement("div");
      countries.className = "bar-countries";
      countries.innerHTML = '<button type="button" class="bar-countries-toggle" aria-expanded="false">' + t("Countries") +
        ' <span class="bar-countries-count"></span><svg viewBox="0 0 10 6" width="10" height="6" aria-hidden="true">' +
        '<path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>';
      barChips = picker.querySelector(".picker-chips").cloneNode(true);
      barChips.classList.add("bar-chips");
      barChips.hidden = true;
      countries.appendChild(barChips);
      bar.querySelector(".section-bar-inner").appendChild(countries);
      countriesToggle = countries.querySelector("button");
    }
    function setCountries(open) {
      if (!countries) return;
      barChips.hidden = !open;
      countriesToggle.setAttribute("aria-expanded", String(open));
    }
    if (countries) {
      countriesToggle.addEventListener("click", function () { setMenu(false); setCountries(barChips.hidden); });
      document.addEventListener("click", function (e) { if (!countries.contains(e.target)) setCountries(false); });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !barChips.hidden) { setCountries(false); countriesToggle.focus(); }
      });
    }
    var copies = links.map(function (a) {
      var m = document.createElement("a");
      m.href = a.getAttribute("href");
      m.textContent = a.textContent;
      if (a.classList.contains("has-new")) { m.className = "has-new"; m.title = a.title; }
      menu.appendChild(m);
      return m;
    });
    document.body.appendChild(bar);
    if (countries) renderChips();      // the copies' state and the count, now they are in the page

    function setMenu(open) {
      menu.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
    }
    toggle.addEventListener("click", function () { setCountries(false); setMenu(menu.hidden); });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("click", function (e) { if (!bar.contains(e.target)) setMenu(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !menu.hidden) { setMenu(false); toggle.focus(); }
    });

    var pending = false;
    function update() {
      pending = false;
      var past = nav.getBoundingClientRect().bottom < 0;
      bar.hidden = !past;
      if (!past) { setMenu(false); setCountries(false); }
      var at = -1;
      for (var i = 0; i < heads.length; i++) if (heads[i].getBoundingClientRect().top < 90) at = i;
      [links, copies].forEach(function (group) {
        group.forEach(function (a, i) {
          a.classList.toggle("is-current", i === at);
          if (i === at) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
        });
      });
      current.textContent = links[Math.max(at, 0)].textContent;
    }
    window.addEventListener("scroll", function () {
      if (!pending) { pending = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  })();

  (function () {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "to-top";
    button.hidden = true;
    button.innerHTML = '<svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M6 10V2M2 6l4-4 4 4" ' +
      'fill="none" stroke="currentColor" stroke-width="1.6"/></svg>' + t("Top");
    button.setAttribute("aria-label", t("Back to the top of the page"));
    document.body.appendChild(button);
    var still = window.matchMedia("(prefers-reduced-motion: reduce)");
    button.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: still.matches ? "auto" : "smooth" });
      var skip = document.querySelector(".brand");
      if (skip) skip.focus({ preventScroll: true });
    });
    function check() { button.hidden = window.scrollY < window.innerHeight * 1.5; }
    window.addEventListener("scroll", check, { passive: true });
    check();
  })();

  // Redraw after a resize settles: whether end labels fit depends on the chart's width.
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawAll, 250);
  });
})();
