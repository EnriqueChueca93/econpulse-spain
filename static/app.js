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

  function token(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  function fmt(v, spec, signed) {
    var s = Math.abs(v).toLocaleString("en-GB", { minimumFractionDigits: spec.decimals, maximumFractionDigits: spec.decimals });
    var sign = v < 0 ? "−" : (signed && v > 0 ? "+" : "");
    return sign + s + (spec.unit === "%" ? "%" : spec.unit === "k" ? "k" : "");
  }

  function hoverFormat(spec) {
    var d = ":" + (spec.kind === "bar" ? "+" : "") + "." + spec.decimals + "f";
    var suffix = spec.unit === "%" ? "%" : spec.unit === "k" ? "k" : "";
    return d + "}" + suffix;
  }

  function draw(spec) {
    var el = document.getElementById("chart-" + spec.id);
    if (!el || !window.Plotly) return;
    // Fixed slot order, never cycled: a spec has at most three series.
    var colors = [token("--series-1"), token("--series-2"), token("--series-3")];
    var surface = token("--surface"), ink = token("--text"), ink2 = token("--text-2");
    var muted = token("--muted"), grid = token("--grid"), axis = token("--axis");
    var multi = spec.series.length > 1;

    var traces = [];
    var annotations = [];
    spec.series.forEach(function (s, i) {
      var color = colors[i];
      // Value leads, name follows; the colored key comes from Plotly's line swatch.
      var template = "<b>%{y" + hoverFormat(spec) + "</b>  " + s.name + "<extra></extra>";
      if (spec.kind === "bar") {
        traces.push({ type: "bar", x: s.x, y: s.y, name: s.name, marker: { color: color }, hovertemplate: template });
        return;
      }
      traces.push({
        type: "scatter", mode: "lines", x: s.x, y: s.y, name: s.name,
        line: { color: color, width: 2, shape: "linear" }, hovertemplate: template
      });
      // End dot with a surface ring, and a direct label in text ink.
      var lastX = s.x[s.x.length - 1], lastY = s.y[s.y.length - 1];
      traces.push({
        type: "scatter", mode: "markers", x: [lastX], y: [lastY], showlegend: false, hoverinfo: "skip",
        marker: { size: 9, color: color, line: { width: 2, color: surface } }
      });
      if (multi) {
        // In the right margin (paper x = 1), so the label doesn't stretch the date axis.
        annotations.push({
          x: 1, xref: "paper", y: lastY, yref: "y", text: s.name + " " + fmt(lastY, spec),
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

    var layout = {
      paper_bgcolor: surface, plot_bgcolor: surface,
      font: { family: token("--sans") || "system-ui, sans-serif", size: 12, color: ink2 },
      margin: { l: 44, r: multi || shapes.length ? 96 : 14, t: multi ? 30 : 10, b: 30 },
      showlegend: multi,
      legend: { orientation: "h", x: 0, xanchor: "left", y: 1.02, yanchor: "bottom", font: { size: 12, color: ink2 } },
      hovermode: "x unified",
      hoverlabel: { bgcolor: surface, bordercolor: grid, font: { color: ink, size: 12 } },
      xaxis: {
        type: "date", showgrid: false, showline: true, linecolor: axis, ticks: "", fixedrange: true,
        hoverformat: spec.date_format || "%b %Y",
        tickfont: { color: muted }, showspikes: true, spikemode: "across", spikethickness: 1,
        spikecolor: axis, spikedash: "solid", spikesnap: "cursor"
      },
      yaxis: {
        gridcolor: grid, gridwidth: 1, zeroline: spec.kind === "bar", zerolinecolor: axis, zerolinewidth: 1,
        fixedrange: true, tickfont: { color: muted }, ticksuffix: spec.unit === "%" ? "%" : spec.unit === "k" ? "k" : "",
        automargin: true
      },
      bargap: 0.3, barcornerradius: 4,
      annotations: annotations, shapes: shapes
    };
    var config = {
      displaylogo: false, responsive: true,
      modeBarButtonsToRemove: ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d",
        "resetScale2d", "toggleSpikelines", "hoverClosestCartesian", "hoverCompareCartesian"],
      toImageButtonOptions: { filename: "econpulse-" + spec.id, scale: 2 }
    };
    window.Plotly.react(el, traces, layout, config);
  }

  // A plain table under each chart, so every value is readable without hovering.
  function fillTable(spec) {
    var holder = document.querySelector('.chart-data[data-chart="' + spec.id + '"]');
    if (!holder || holder.querySelector("table")) return;
    var table = document.createElement("table");
    var head = table.createTHead().insertRow();
    ["Date"].concat(spec.series.map(function (s) { return s.name; })).forEach(function (h) {
      var th = document.createElement("th"); th.scope = "col"; th.textContent = h; head.appendChild(th);
    });
    var body = table.createTBody();
    var dates = spec.series[0].x;
    var start = Math.max(0, dates.length - 12);
    for (var i = dates.length - 1; i >= start; i--) {
      var row = body.insertRow();
      row.insertCell().textContent = dates[i];
      spec.series.forEach(function (s) {
        var j = s.x.indexOf(dates[i]);
        row.insertCell().textContent = j >= 0 ? fmt(s.y[j], spec, spec.kind === "bar") : "–";
      });
    }
    var caption = document.createElement("p");
    caption.className = "note";
    caption.textContent = "Latest 12 observations.";
    holder.appendChild(table);
    holder.appendChild(caption);
  }

  function drawAll() {
    specs.forEach(draw);
  }

  specs.forEach(fillTable);
  drawAll();
})();
