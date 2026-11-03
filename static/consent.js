/* Macroscope Spain: the cookie banner and Google Analytics, which loads only after a visitor accepts it.
 *
 * Loaded only when config.py switches analytics on (econpulse/build.py, web_analytics). Nothing reaches Google before
 * a "yes": no script, no request, no cookie. The answer is kept in local storage ("ep-consent", with its date) and
 * asked again after a year, inside the AEPD's 24 months. "Reject", at any time from the footer's "Cookie settings",
 * stops Google Analytics on the page and deletes its cookies. The rest of the site sends feature events through
 * window.EPconsent.track, which does nothing without consent.
 */
(function () {
  "use strict";

  var box = document.getElementById("consent");
  if (!box) return;
  var ID = box.getAttribute("data-ga") || "", PATH = box.getAttribute("data-path") || "/";
  var KEY = "ep-consent", YEAR = 365 * 24 * 3600;      // seconds: the answer and the cookies both last a year
  var loaded = false;

  function stored() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || "null");
      if (c && (c.choice === "yes" || c.choice === "no") && Date.now() - c.at < YEAR * 1000) return c.choice;
    } catch (e) { /* no answer kept */ }
    return null;
  }

  function remember(choice) {
    try { localStorage.setItem(KEY, JSON.stringify({ choice: choice, at: Date.now() })); } catch (e) { /* this visit only */ }
  }

  function load() {
    if (!/^G-[A-Z0-9]+$/.test(ID)) return;
    window["ga-disable-" + ID] = false;
    if (loaded) {                                       // rejected, then accepted again on the same page
      window.gtag("consent", "update", { analytics_storage: "granted" });
      return;
    }
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    // Analytics only: every advertising use is refused, whatever the property's own settings.
    window.gtag("consent", "default", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied",
                                        ad_personalization: "denied" });
    window.gtag("js", new Date());
    window.gtag("config", ID, {
      cookie_path: PATH, cookie_expires: YEAR, cookie_flags: "SameSite=Lax;Secure",
      allow_google_signals: false, allow_ad_personalization_signals: false
    });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(ID);
    document.head.appendChild(s);
  }

  // Google Analytics' cookies on this site: _ga, and _ga_ followed by the property's code. Deleting is the only
  // thing this file ever does with cookies.
  function deleteCookies() {
    document.cookie.split(";").forEach(function (part) {
      var name = part.split("=")[0].trim();
      if (name !== "_ga" && name.indexOf("_ga_") !== 0) return;
      [PATH, "/"].forEach(function (path) {
        ["", "; domain=" + location.hostname, "; domain=." + location.hostname].forEach(function (domain) {
          document.cookie = name + "=; Max-Age=0; path=" + path + domain;
        });
      });
    });
  }

  function stop() {
    if (loaded) {
      window.gtag("consent", "update", { analytics_storage: "denied" });
      window["ga-disable-" + ID] = true;               // no more hits from this page
    }
    deleteCookies();
  }

  // ---------------------------------------------------------------- the banner
  var status = box.querySelector(".consent-status");

  function open(fromSettings) {
    var choice = stored();
    if (status) {
      status.textContent = choice ? box.getAttribute(choice === "yes" ? "data-accepted" : "data-rejected") : "";
      status.hidden = !choice;
    }
    box.hidden = false;
    document.body.style.paddingBottom = box.offsetHeight + "px";   // never hides the end of the page
    if (fromSettings) { var first = box.querySelector("button"); if (first) first.focus(); }
  }

  function close() {
    box.hidden = true;
    document.body.style.paddingBottom = "";
  }

  function answer(choice) {
    remember(choice);
    close();
    if (choice === "yes") load(); else stop();
  }

  box.querySelector("[data-consent='yes']").addEventListener("click", function () { answer("yes"); });
  box.querySelector("[data-consent='no']").addEventListener("click", function () { answer("no"); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-cookie-settings]"), function (b) {
    b.addEventListener("click", function () { open(true); });
  });
  window.addEventListener("resize", function () { if (!box.hidden) document.body.style.paddingBottom = box.offsetHeight + "px"; });

  var choice = stored();
  if (choice === "yes") load();
  else if (choice === null) { deleteCookies(); open(false); }   // a year on, or never asked: old cookies go too

  window.EPconsent = {
    // A feature event (what was used, never what was typed), sent only with consent.
    track: function (name, params) {
      if (loaded && stored() === "yes") window.gtag("event", name, params || {});
    },
    // "Forget my choices" on the About page: the answer goes, and so do the cookies; the banner returns.
    reset: function () { stop(); open(false); }
  };
})();
