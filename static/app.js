// Renders the home page from window.EP.snapshot (written by `python -m econpulse build`).
// Data arrives through a <script> tag rather than fetch(), so the page works when opened from disk.
(function () {
  "use strict";

  var snap = window.EP && window.EP.snapshot;
  if (!snap) {
    document.getElementById("tiles").textContent = "No data yet: run update.bat (or python -m econpulse update).";
    return;
  }

  var SECTION_NAMES = {
    gdp: "GDP", labour: "Labour market", wages: "Wages", inflation: "Inflation",
    financial: "Financial", ecb: "ECB", fiscal: "Fiscal", activity: "Activity",
    housing: "Housing", international: "International"
  };

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function badges(item) {
    var out = [];
    if (item.flash) out.push(["flash", "flash estimate"]);
    if (item.status === "stale") out.push(["warn", "stale: last update failed"]);
    if (item.status === "error") out.push(["warn", "no data"]);
    if (item.status === "ok" && item.out_of_date) out.push(["warn", "not updating"]);
    return out.map(function (b) { return el("span", "badge badge-" + b[0], b[1]); });
  }

  var byId = {};
  snap.indicators.forEach(function (item) { byId[item.id] = item; });

  // As-of line in the header, in the viewer's local time.
  if (snap.data_as_of) {
    var asof = new Date(snap.data_as_of);
    document.getElementById("asof").textContent = "Data as of " + asof.toLocaleDateString("en-GB", {
      day: "numeric", month: "short", year: "numeric"
    });
  }

  // Key indicator tiles.
  var tiles = document.getElementById("tiles");
  snap.tiles.forEach(function (id) {
    var item = byId[id];
    var head = item.headline;
    var tile = el("a", "tile");
    if (item.source_url) { tile.href = item.source_url; tile.target = "_blank"; tile.rel = "noopener"; }
    tile.title = item.label_es + (item.notes ? " — " + item.notes : "");
    tile.appendChild(el("div", "tile-label", item.label));
    var value = el("div", "tile-value", head ? head.display : "–");
    if (head && head.label) value.appendChild(el("span", "tile-unit", " " + head.label));
    tile.appendChild(value);
    var meta = el("div", "tile-meta");
    meta.appendChild(el("span", "tile-period", head ? head.period : ""));
    if (item.subline) meta.appendChild(el("span", "tile-sub", item.subline));
    tile.appendChild(meta);
    var b = badges(item);
    if (b.length) {
      var row = el("div", "tile-badges");
      b.forEach(function (x) { row.appendChild(x); });
      tile.appendChild(row);
    }
    tiles.appendChild(tile);
  });

  // Full table, grouped by section.
  var tbody = document.querySelector("#all-indicators tbody");
  Object.keys(SECTION_NAMES).forEach(function (section) {
    var items = snap.indicators.filter(function (i) { return i.section === section; });
    if (!items.length) return;
    var groupRow = el("tr", "group");
    var groupCell = el("th", null, SECTION_NAMES[section]);
    groupCell.colSpan = 5;
    groupRow.appendChild(groupCell);
    tbody.appendChild(groupRow);

    items.forEach(function (item) {
      var head = item.headline;
      var tr = el("tr");
      var name = el("td");
      name.appendChild(el("div", "ind-name", item.label));
      name.appendChild(el("div", "ind-es", item.label_es));
      badges(item).forEach(function (x) { name.appendChild(x); });
      tr.appendChild(name);
      tr.appendChild(el("td", "num", head ? (head.display + (head.label ? " " + head.label : "")) : "–"));
      tr.appendChild(el("td", "num muted", item.subline || ""));
      tr.appendChild(el("td", "muted", head ? head.period : ""));
      var src = el("td");
      if (item.source_url) {
        var a = el("a", null, item.source);
        a.href = item.source_url; a.target = "_blank"; a.rel = "noopener";
        src.appendChild(a);
      } else {
        src.textContent = item.source;
      }
      tr.appendChild(src);
      tbody.appendChild(tr);
    });
  });
})();
