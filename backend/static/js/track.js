function track(event, payload) {
  payload = payload || {};
  // GA4
  if (typeof gtag === 'function') {
    gtag('event', event, payload);
  }
  // Meta Pixel
  if (typeof fbq === 'function') {
    fbq('trackCustom', event, payload);
  }
}

// Track CTA clicks
document.addEventListener('click', function(e) {
  var el = e.target.closest('[data-track]');
  if (!el) return;
  var eventName = el.getAttribute('data-track');
  var eventData = el.getAttribute('data-track-payload');
  try { eventData = eventData ? JSON.parse(eventData) : {}; } catch(err) { eventData = {}; }
  track(eventName, eventData);
});
