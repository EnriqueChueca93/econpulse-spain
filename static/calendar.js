// The Calendar page's next three days (Batch 32c): the build writes a fortnight of working days, each shaded by
// its number of releases; this picks the three from the viewer's own date and time in Madrid (today while it
// still has releases to come) and shows the releases of the day clicked.
(function () {
  "use strict";
  var box = document.getElementById("cal-soon");
  if (!box) return;
  var cells = Array.prototype.slice.call(box.querySelectorAll(".cal-day"));

  var parts = {};
  new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Madrid", year: "numeric", month: "2-digit", day: "2-digit",
                                     hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
    .formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
  var today = parts.year + "-" + parts.month + "-" + parts.day, now = parts.hour + ":" + parts.minute;
  var next = new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day + 1)).toISOString().slice(0, 10);

  function date(c) { return c.getAttribute("data-date"); }
  function count(c) { return +c.getAttribute("data-count"); }
  var shown = cells.filter(function (c) {
    return date(c) > today || (date(c) === today && c.getAttribute("data-last") > now);
  }).slice(0, 3);
  if (!shown.length) { box.hidden = true; return; }      // a build too old to know the coming days

  cells.forEach(function (c) {
    c.hidden = shown.indexOf(c) < 0;
    c.querySelector(".cal-tag").textContent = date(c) === today ? "Today" : date(c) === next ? "Tomorrow" : "";
    c.setAttribute("aria-label", c.getAttribute("data-long") + ": " +
                   (count(c) ? count(c) + " release" + (count(c) > 1 ? "s" : "") : "no releases"));
  });

  function pick(cell) {
    cells.forEach(function (c) {
      c.setAttribute("aria-pressed", String(c === cell));
      document.getElementById(c.getAttribute("aria-controls")).hidden = c !== cell;
    });
  }
  pick(shown.filter(count)[0] || shown[0]);              // the first day with releases opens to start with
  box.querySelector(".cal-heat").addEventListener("click", function (e) {
    var c = e.target.closest(".cal-day");
    if (c) pick(c);
  });

  // Nothing in all three: say when the next release is.
  if (!shown.some(count)) {
    var last = date(shown[shown.length - 1]);
    var later = cells.filter(function (c) { return date(c) > last && count(c); })[0];
    var note = box.querySelector(".cal-none");
    note.textContent = "Nothing scheduled in the next three working days." + (later
      ? " The next release is " + later.getAttribute("data-first") + ", on " + later.getAttribute("data-long") + "."
      : "");
    note.hidden = false;
  }
})();
