// Lightweight event tracking — consent-gated.
// GA4 + Meta Pixel are loaded by consent.js after user accepts cookies.
// Events fired before consent are queued and replayed once.
(function() {
  var queue = [];
  var consentGranted = false;

  // Map our internal event names to FB Pixel STANDARD events.
  // Everything else falls back to fbq('trackCustom', ...) only.
  var FB_STANDARD_EVENTS = {
    'lead_form_success':    'Lead',
    'telegram_click':       'Contact',
    'demo_start':           'ViewContent',
    'demo_scenario_select': 'ViewContent',
    'hero_cta_click':       'ViewContent',
    'demo_cta_click':       'InitiateCheckout',
    'pricing_plan_click':   'InitiateCheckout'
  };

  // Per-page dedup for events that should fire at most once per pageview.
  // (lead_form_success is deduped per lead_id; depth events have their own flag below.)
  var firedOnce = {};
  var SINGLE_FIRE = {
    'lead_form_success': true  // additional safety on top of forms.js
  };

  function autoParams(extra) {
    var html = document.documentElement;
    var p = {
      page_path: window.location.pathname,
      page_location: window.location.href,
      language: html.getAttribute('lang') || ''
    };
    if (extra) {
      for (var k in extra) {
        if (Object.prototype.hasOwnProperty.call(extra, k)) p[k] = extra[k];
      }
    }
    return p;
  }

  function fireGA(name, payload) {
    if (typeof window.gtag === 'function') {
      try { window.gtag('event', name, payload); } catch (e) {}
    }
  }
  function fireFB(name, payload) {
    if (typeof window.fbq !== 'function') return;
    try {
      var standard = FB_STANDARD_EVENTS[name];
      var fbPayload = {};
      // Only forward whitelisted, non-PII fields to Pixel
      var ALLOWED = ['plan_name', 'scenario_name', 'cta_location', 'lead_type', 'business_type', 'language'];
      for (var i = 0; i < ALLOWED.length; i++) {
        var k = ALLOWED[i];
        if (payload && payload[k] != null) fbPayload[k] = payload[k];
      }
      // Use eventID for Lead → enables future Conversions API dedup
      var opts = {};
      if (standard === 'Lead' && payload && payload.lead_id) {
        opts.eventID = payload.lead_id;
      }
      if (standard) {
        if (Object.keys(opts).length) {
          window.fbq('track', standard, fbPayload, opts);
        } else {
          window.fbq('track', standard, fbPayload);
        }
      }
      // Granular custom event with the original name
      window.fbq('trackCustom', name, fbPayload);
    } catch (e) {}
  }

  function fire(name, payload) {
    fireGA(name, payload);
    fireFB(name, payload);
  }

  window.track = function(event, payload) {
    if (SINGLE_FIRE[event] && firedOnce[event]) return;
    firedOnce[event] = true;

    var enriched = autoParams(payload || {});
    if (consentGranted) {
      fire(event, enriched);
    } else {
      queue.push([event, enriched]);
      if (queue.length > 50) queue.shift();
    }
  };

  // Called by consent.js once analytics are loaded
  window.__onAnalyticsReady = function() {
    consentGranted = true;
    while (queue.length) {
      var ev = queue.shift();
      fire(ev[0], ev[1]);
    }
  };

  // Click events via data-track
  document.addEventListener('click', function(e) {
    var el = e.target.closest('[data-track]');
    if (!el) return;
    var name = el.getAttribute('data-track');
    var raw = el.getAttribute('data-track-payload');
    var data = {};
    if (raw) { try { data = JSON.parse(raw); } catch (err) { data = {}; } }
    window.track(name, data);
  });

  // FAQ open
  document.addEventListener('click', function(e) {
    var btn = e.target.closest('[data-faq-toggle]');
    if (!btn) return;
    window.track('faq_open', { id: btn.getAttribute('data-faq-toggle') });
  });

  // Scroll depth (50% / 90%) — once per page
  var depthFired = { '50': false, '90': false };
  function getDepth() {
    var doc = document.documentElement;
    var top = window.pageYOffset || doc.scrollTop;
    var height = (doc.scrollHeight || document.body.scrollHeight) - window.innerHeight;
    if (height <= 0) return 0;
    return Math.min(100, Math.round((top / height) * 100));
  }
  window.addEventListener('scroll', function() {
    var d = getDepth();
    if (!depthFired['50'] && d >= 50) { depthFired['50'] = true; window.track('scroll_50'); }
    if (!depthFired['90'] && d >= 90) { depthFired['90'] = true; window.track('scroll_90'); }
  }, { passive: true });

  // Mobile sticky CTA: reveal after small scroll, hide on contact page
  document.addEventListener('DOMContentLoaded', function() {
    var sticky = document.getElementById('mobile-sticky');
    if (!sticky) return;
    if (document.body.getAttribute('data-page') === 'contact') {
      sticky.remove();
      return;
    }
    var revealed = false;
    function reveal() {
      if (revealed) return;
      revealed = true;
      sticky.classList.remove('opacity-0', 'translate-y-3');
      sticky.classList.add('opacity-100', 'translate-y-0');
    }
    window.addEventListener('scroll', function() {
      if (window.pageYOffset > 200) reveal();
    }, { passive: true });
    setTimeout(function() {
      if ((document.documentElement.scrollHeight - window.innerHeight) < 400) reveal();
    }, 4000);
  });
})();
