/**
 * GA4 Tracker — Script leve para LP/VSL
 * SEM GA4/GTM na página. Envia tudo server-side via API própria.
 *
 * Captura automaticamente:
 *   - page_view (ao carregar)
 *   - scroll_depth (25%, 50%, 75%, 90%)
 *   - cta_click (em <a> e <button>)
 *
 * Expõe função pública:
 *   window.trackVslProgress(percent, seconds)
 *
 * CONFIGURAÇÃO:
 *   <script>window.GA4_TRACKER_URL = "https://seudominio.com";</script>
 *   <script src="https://seudominio.com/static/tracker.js"></script>
 */
(function () {
  "use strict";

  var API_URL = window.GA4_TRACKER_URL || "";
  if (!API_URL) {
    console.warn("[GA4 Tracker] window.GA4_TRACKER_URL não definido.");
    return;
  }
  API_URL = API_URL.replace(/\/+$/, "");

  // ── Helpers ────────────────────────────────────────────────────
  function uuid() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function getParam(name) {
    try {
      return new URL(window.location.href).searchParams.get(name) || "";
    } catch (_) {
      return "";
    }
  }

  // ── IDs persistentes ──────────────────────────────────────────
  var CLIENT_ID = localStorage.getItem("_ga4t_cid");
  if (!CLIENT_ID) {
    CLIENT_ID = uuid();
    localStorage.setItem("_ga4t_cid", CLIENT_ID);
  }

  var SESSION_ID = sessionStorage.getItem("_ga4t_sid");
  if (!SESSION_ID) {
    SESSION_ID = String(Math.floor(Date.now() / 1000));
    sessionStorage.setItem("_ga4t_sid", SESSION_ID);
  }

  // ── Visitor Key (clickid / subid / tid / sub1 / rtkcid) ───────
  var VISITOR_KEY =
    getParam("clickid") ||
    getParam("subid") ||
    getParam("tid") ||
    getParam("sub1") ||
    getParam("rtkcid") ||
    "";

  if (VISITOR_KEY) {
    sessionStorage.setItem("_ga4t_vk", VISITOR_KEY);
  } else {
    VISITOR_KEY = sessionStorage.getItem("_ga4t_vk") || "";
  }

  if (!VISITOR_KEY) {
    VISITOR_KEY = "anon_" + CLIENT_ID.substring(0, 12);
  }

  // ── UTMs + gclid ─────────────────────────────────────────────
  var UTM_SOURCE = getParam("utm_source");
  var UTM_MEDIUM = getParam("utm_medium");
  var UTM_CAMPAIGN = getParam("utm_campaign");
  var GCLID = getParam("gclid");

  // ── Core send ─────────────────────────────────────────────────
  function sendEvent(eventName, extra) {
    var data = {
      page_location: window.location.href,
      page_title: document.title || "",
    };

    if (UTM_SOURCE) data.utm_source = UTM_SOURCE;
    if (UTM_MEDIUM) data.utm_medium = UTM_MEDIUM;
    if (UTM_CAMPAIGN) data.utm_campaign = UTM_CAMPAIGN;
    if (GCLID) data.gclid = GCLID;

    if (extra && typeof extra === "object") {
      for (var k in extra) {
        if (extra.hasOwnProperty(k)) data[k] = extra[k];
      }
    }

    var payload = {
      event: eventName,
      client_id: CLIENT_ID,
      session_id: SESSION_ID,
      visitor_key: VISITOR_KEY,
      data: data,
    };

    if (navigator.sendBeacon) {
      var blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
      navigator.sendBeacon(API_URL + "/ga4/event", blob);
    } else {
      try {
        fetch(API_URL + "/ga4/event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          keepalive: true,
        });
      } catch (_) {}
    }
  }

  // ── page_view ─────────────────────────────────────────────────
  sendEvent("page_view");

  // ── scroll_depth ──────────────────────────────────────────────
  var scrollFired = {};
  var scrollThresholds = [25, 50, 75, 90];

  function onScroll() {
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    var docHeight =
      Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) -
      window.innerHeight;
    if (docHeight <= 0) return;
    var pct = Math.round((scrollTop / docHeight) * 100);

    for (var i = 0; i < scrollThresholds.length; i++) {
      var t = scrollThresholds[i];
      if (pct >= t && !scrollFired[t]) {
        scrollFired[t] = true;
        sendEvent("scroll_depth", { percent_scrolled: t });
      }
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });

  // ── cta_click ─────────────────────────────────────────────────
  document.addEventListener("click", function (e) {
    var el = e.target;
    while (el && el !== document) {
      var tag = el.tagName;
      if (tag === "A" || tag === "BUTTON") {
        sendEvent("cta_click", {
          button_text: (el.innerText || "").substring(0, 100),
          link_url: el.href || "",
        });
        return;
      }
      el = el.parentElement;
    }
  });

  // ── vsl_progress (função pública) ─────────────────────────────
  window.trackVslProgress = function (percent, seconds) {
    sendEvent("vsl_progress", {
      video_percent: percent,
      video_current_time: seconds,
    });
  };
})();
