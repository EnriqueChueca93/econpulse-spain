// EconPulse Spain: sorting the central bank stance matrix (site/stance.html).
(function () {
  "use strict";
  var table = document.getElementById("stance-table");
  if (!table) return;
  var body = table.tBodies[0];
  var buttons = document.querySelectorAll("[data-sort]");

  function sortBy(key) {
    var rows = Array.prototype.slice.call(body.rows);
    rows.sort(function (a, b) {
      var x = a.getAttribute("data-" + key), y = b.getAttribute("data-" + key);
      if (key === "country") return x.localeCompare(y);
      if (key === "rate") return parseFloat(y) - parseFloat(x);   // highest first
      return parseFloat(x) - parseFloat(y);                        // order, days until the meeting
    });
    rows.forEach(function (row) { body.appendChild(row); });
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-sort") === key ? "true" : "false");
    });
  }

  Array.prototype.forEach.call(buttons, function (btn) {
    btn.addEventListener("click", function () { sortBy(btn.getAttribute("data-sort")); });
  });
})();
