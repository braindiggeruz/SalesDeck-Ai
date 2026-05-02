// Lightweight event tracking — no-op safe if GA4/Pixel not loaded
(function() {
  function safeGtag(event, payload) {
    if (typeof window.gtag === 'function') {
      try { window.gtag('event', event, payload); } catch (e) {}
    }
  }
  function safeFbq(event, payload) {
    if (typeof window.fbq === 'function') {
      try { window.fbq('trackCustom', event, payload); } catch (e) {}
    }
  }

  window.track = function(event, payload) {
    payload = payload || {};
    safeGtag(event, payload);
    safeFbq(event, payload);
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

  // Mobile sticky CTA: reveal after small scroll, hide on form/contact pages where it overlaps
  document.addEventListener('DOMContentLoaded', function() {
    var sticky = document.getElementById('mobile-sticky');
    if (!sticky) return;
    // hide on contact page (sticky overlaps form CTA)
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
    // also reveal after 4s for short pages
    setTimeout(function() {
      if ((document.documentElement.scrollHeight - window.innerHeight) < 400) reveal();
    }, 4000);
  });
})();
