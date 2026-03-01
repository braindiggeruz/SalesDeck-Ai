(function() {
  var CONSENT_KEY = 'salesdesk_consent';

  function getConsent() {
    try { return localStorage.getItem(CONSENT_KEY); } catch(e) { return null; }
  }

  function setConsent(value) {
    try { localStorage.setItem(CONSENT_KEY, value); } catch(e) {}
  }

  function hideBanner() {
    var banner = document.getElementById('consent-banner');
    if (banner) banner.classList.add('hidden');
  }

  function loadAnalytics() {
    var ga4Id = document.documentElement.getAttribute('data-ga4');
    var pixelId = document.documentElement.getAttribute('data-pixel');

    if (ga4Id) {
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ga4Id;
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      window.gtag = function() { dataLayer.push(arguments); };
      gtag('js', new Date());
      gtag('config', ga4Id, { send_page_view: true });
    }

    if (pixelId) {
      !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
      n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
      n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
      t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
      document,'script','https://connect.facebook.net/en_US/fbevents.js');
      fbq('init', pixelId);
      fbq('track', 'PageView');
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    var consent = getConsent();

    if (consent === 'accepted') {
      loadAnalytics();
      hideBanner();
      return;
    }

    if (consent === 'declined') {
      hideBanner();
      return;
    }

    // Show banner
    var banner = document.getElementById('consent-banner');
    if (banner) banner.classList.remove('hidden');

    var acceptBtn = document.getElementById('consent-accept');
    var declineBtn = document.getElementById('consent-decline');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function() {
        setConsent('accepted');
        hideBanner();
        loadAnalytics();
      });
    }
    if (declineBtn) {
      declineBtn.addEventListener('click', function() {
        setConsent('declined');
        hideBanner();
      });
    }
  });
})();
