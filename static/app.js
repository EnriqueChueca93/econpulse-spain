// EconPulse Spain: theme toggle and charts.
// Pages are plain HTML; this script only adds the light/dark switch and draws the
// charts from window.EP.charts (written by `python -m econpulse build`).
(function () {
  "use strict";

  var root = document.documentElement;
  var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

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

  // ---------------------------------------------------------------- charts
  var specs = (window.EP && window.EP.charts) || [];
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

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
    return MONTHS[m - 1] + " " + y;
  }

  function hoverDate(spec) {
    if (spec.date_format) return spec.date_format;
    return spec.freq === "Q" ? "Q%q %Y" : spec.freq === "D" ? "%-d %b %Y" : "%b %Y";
  }

  var CONFIG_BASE = {
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
    el.style.height = Math.max(220, s.x.length * 22 + 56) + "px";
    var format = ":." + spec.decimals + "f}" + suffix(spec);
    var traces = [{
      type: "bar", orientation: "h", x: s.y, y: s.x, showlegend: false,
      marker: { color: s.x.map(function (label) { return label === spec.highlight ? ink : token("--series-1"); }) },
      hovertemplate: "<b>%{x" + format + "</b>  %{y}<extra></extra>"
    }];
    var shapes = [], annotations = [];
    (spec.ref_lines || []).forEach(function (r) {
      shapes.push({ type: "line", yref: "paper", y0: 0, y1: 1, x0: r.y, x1: r.y, line: { color: ink2, width: 1, dash: "dot" } });
      annotations.push({ x: r.y, xref: "x", y: 1, yref: "paper", yanchor: "bottom", showarrow: false,
        text: r.label + " " + fmt(r.y, spec), font: { size: 11, color: ink2 } });
    });
    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 10, r: 18, t: annotations.length ? 24 : 8, b: 30 },
      hovermode: "closest", hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      yaxis: { type: "category", autorange: "reversed", automargin: true, fixedrange: true, ticks: "",
        tickfont: { color: ink2, size: 12 } },
      xaxis: { gridcolor: grid, zeroline: true, zerolinecolor: axis, fixedrange: true, tickfont: { color: muted },
        ticksuffix: suffix(spec), automargin: true },
      bargap: 0.3, barcornerradius: 3, shapes: shapes, annotations: annotations
    };
    var config = Object.assign({ toImageButtonOptions: { filename: "econpulse-" + spec.id, scale: 2 } }, CONFIG_BASE);
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
    var config = Object.assign({ toImageButtonOptions: { filename: "econpulse-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config);
  }

  function draw(spec) {
    var el = document.getElementById("chart-" + spec.id);
    if (!el || !window.Plotly) return;
    if (spec.kind === "hbar") return drawRanking(el, spec);
    if (spec.kind === "xy") return drawXY(el, spec);
    // Fixed slot order, never cycled: a spec has at most three palette series.
    var colors = [token("--series-1"), token("--series-2"), token("--series-3")];
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis");
    var multi = spec.series.length > 1;
    // Curves (yields by maturity, rates by horizon) have a category axis instead of dates.
    var category = spec.x_kind === "category";
    // On narrow (phone-width) charts the legend names the lines; end labels would squeeze the plot.
    var endLabels = multi && el.clientWidth >= 480;
    var valueFormat = ":" + (spec.signed ? "+" : "") + "." + spec.decimals + "f}" + suffix(spec);

    // Dense bar charts (monthly bars over many years) drop the gaps and rounding, which would read as stripes.
    var dense = spec.series[0].x.length > 60;
    var traces = [];
    var annotations = [];
    var slot = 0;
    spec.series.forEach(function (s) {
      // A total drawn in text colour takes no palette slot.
      var color = s.color === "ink" ? ink : colors[slot++];
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
    var config = Object.assign({ toImageButtonOptions: { filename: "econpulse-" + spec.id, scale: 2 } }, CONFIG_BASE);
    window.Plotly.react(el, traces, layout, config).then(function () { spreadLabels(el); });
  }

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

  // A plain table under each chart, so every value is readable without hovering.
  function fillTable(spec) {
    var holder = document.querySelector('.chart-data[data-chart="' + spec.id + '"]');
    if (!holder || holder.querySelector("table")) return;
    var table = document.createElement("table");
    var category = spec.x_kind === "category";
    var head = table.createTHead().insertRow();
    if (spec.kind === "xy") return fillXYTable(spec, holder, table, head);
    [spec.x_title || "Date"].concat(spec.series.map(function (s) { return s.name; })).forEach(function (h) {
      var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
    });
    // Curves: every point in order. Time series: every date any series has (they can
    // differ in frequency), newest first.
    var seen = {}, dates = [];
    spec.series.forEach(function (s) {
      s.x.forEach(function (d) { if (!seen[d]) { seen[d] = true; dates.push(d); } });
    });
    if (!category) dates = dates.sort().reverse().slice(0, 12);
    var body = table.createTBody();
    dates.forEach(function (d) {
      var row = body.insertRow();
      row.insertCell().textContent = category ? d : dateLabel(d, spec.freq);
      spec.series.forEach(function (s) {
        var j = s.x.indexOf(d);
        row.insertCell().textContent = j >= 0 && s.y[j] !== null ? fmt(s.y[j], spec, spec.signed) : "–";
      });
    });
    var caption = document.createElement("p");
    caption.className = "note";
    caption.textContent = category ? "All points." : "Latest " + dates.length + " dates.";
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
    caption.textContent = "Latest 12 periods.";
    holder.appendChild(table);
    holder.appendChild(caption);
  }

  function drawAll() {
    specs.forEach(draw);
  }

  specs.forEach(fillTable);
  drawAll();

  // For pages that build charts in the browser (the tools): draw a spec now, and again
  // whenever the theme or the window size changes, like the charts written by the build.
  window.EP = window.EP || {};
  window.EP.render = function (spec) {
    for (var i = 0; i < specs.length; i++) {
      if (specs[i].id === spec.id) { specs[i] = spec; draw(spec); return; }
    }
    specs.push(spec);
    draw(spec);
  };
  window.EP.fmt = fmt;

  // Redraw after a resize settles: whether end labels fit depends on the chart's width.
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawAll, 250);
  });
})();
