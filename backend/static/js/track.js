// Lightweight event tracking — consent-gated.
// GA4 + Meta Pixel are loaded by consent.js after user accepts cookies.
// All track() calls before consent are queued and replayed.
(function() {
  var queue = [];
  var consentGranted = false;

  // Map our internal event names to FB Pixel STANDARD events (better attribution).
  // Everything else falls back to fbq('trackCustom', ...).
  var FB_STANDARD_EVENTS = {
    'lead_form_success': 'Lead',
    'telegram_click':    'Contact',
    'demo_start':        'ViewContent',
    'demo_scenario_select': 'ViewContent',
    'demo_cta_click':    'InitiateCheckout',
    'pricing_plan_click': 'InitiateCheckout',
    'hero_cta_click':    'ViewContent'
  };

  function fireGA(name, payload) {
    if (typeof window.gtag === 'function') {
      try { window.gtag('event', name, payload || {}); } catch (e) {}
    }
  }
  function fireFB(name, payload) {
    if (typeof window.fbq !== 'function') return;
    try {
      var standard = FB_STANDARD_EVENTS[name];
      if (standard) {
        // Pixel standard events accept currency/value when applicable; we omit since price is variable.
        window.fbq('track', standard, payload || {});
      }
      // Always also send a custom event with the original name — useful for granular segmentation.
      window.fbq('trackCustom', name, payload || {});
    } catch (e) {}
  }

  function fire(name, payload) {
    fireGA(name, payload);
    fireFB(name, payload);
  }

  window.track = function(event, payload) {
    payload = payload || {};
    if (consentGranted) {
      fire(event, payload);
    } else {
      // queue until consent (or no-op forever if user declines)
      queue.push([event, payload]);
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

  // Scroll depth (50% / 90%) — fire once per page
  var fired = { '50': false, '90': false };
  function getDepth() {
    var doc = document.documentElement;
    var top = window.pageYOffset || doc.scrollTop;
    var height = (doc.scrollHeight || document.body.scrollHeight) - window.innerHeight;
    if (height <= 0) return 0;
    return Math.min(100, Math.round((top / height) * 100));
  }
  window.addEventListener('scroll', function() {
    var d = getDepth();
    if (!fired['50'] && d >= 50) { fired['50'] = true; window.track('scroll_50'); }
    if (!fired['90'] && d >= 90) { fired['90'] = true; window.track('scroll_90'); }
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
