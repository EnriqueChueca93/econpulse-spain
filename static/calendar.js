// The Calendar page's release map (Batch 32c): the build writes four months of days, each shaded by its number
// of releases; this shows the three from the viewer's own month in Madrid, marks today, and lists the releases of
// the day clicked, opening on the first day with releases still to come.
(function () {
  "use strict";
  var box = document.getElementById("cal-map");
  if (!box) return;

  var parts = {};
  new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Madrid", year: "numeric", month: "2-digit", day: "2-digit",
                                     hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
    .formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
  var today = parts.year + "-" + parts.month + "-" + parts.day, now = parts.hour + ":" + parts.minute;

  var months = Array.prototype.slice.call(box.querySelectorAll(".cal-month"));
  var start = months.map(function (m) { return m.getAttribute("data-month"); }).indexOf(today.slice(0, 7));
  if (start < 0) { box.hidden = true; return; }           // a build too old to know the months ahead
  months.forEach(function (m, i) { m.hidden = i < start || i >= start + 3; });

  Array.prototype.forEach.call(box.querySelectorAll(".cal-cell"), function (c) {
    var d = c.getAttribute("data-date");
    c.classList.toggle("is-past", d < today);
    c.classList.toggle("is-today", d === today);
    if (c.tagName === "BUTTON") c.disabled = d < today;
  });

  var buttons = Array.prototype.slice.call(box.querySelectorAll("button.cal-cell"));
  var grid = box.querySelector(".cal-months"), panel = box.querySelector(".cal-panel");
  // With the months one under another (phones), the day's releases go right under its month.
  function place(b) {
    if (b && getComputedStyle(grid).gridTemplateColumns.split(" ").length === 1) b.closest(".cal-month").after(panel);
    else if (panel.parentNode !== box) grid.after(panel);
  }
  function pick(b) {
    buttons.forEach(function (x) {
      x.setAttribute("aria-pressed", String(x === b));
      document.getElementById(x.getAttribute("aria-controls")).hidden = x !== b;
    });
    place(b);
  }
  var open = buttons.filter(function (b) {
    var d = b.getAttribute("data-date");
    return !b.closest(".cal-month").hidden && (d > today || (d === today && b.getAttribute("data-last") > now));
  })[0];
  pick(open || null);
  box.querySelector(".cal-none").hidden = !!open;
  window.addEventListener("resize", function () { place(box.querySelector('button.cal-cell[aria-pressed="true"]')); });
  box.querySelector(".cal-months").addEventListener("click", function (e) {
    var b = e.target.closest("button.cal-cell");
    if (b && !b.disabled) {
      pick(b);
      box.querySelector(".cal-none").hidden = true;
    }
  });
})();
