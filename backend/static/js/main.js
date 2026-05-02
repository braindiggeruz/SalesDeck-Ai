document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  var menuBtn = document.getElementById('mobile-menu-btn');
  var mobileMenu = document.getElementById('mobile-menu');
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', function() {
      var isHidden = mobileMenu.classList.contains('hidden');
      mobileMenu.classList.toggle('hidden');
      menuBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
    });
  }

  // FAQ accordion
  var faqButtons = document.querySelectorAll('[data-faq-toggle]');
  faqButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = document.getElementById(btn.getAttribute('data-faq-toggle'));
      var icon = btn.querySelector('[data-faq-icon]');
      if (!target) return;
      var isOpen = !target.classList.contains('hidden');
      target.classList.toggle('hidden');
      if (icon) {
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
      }
      btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
    });
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function(a) {
    a.addEventListener('click', function(e) {
      var target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Generic toggle (e.g., "Add message" on contact form)
  document.querySelectorAll('[data-toggle-target]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = document.getElementById(btn.getAttribute('data-toggle-target'));
      if (!target) return;
      target.classList.toggle('hidden');
      btn.classList.toggle('opacity-50');
    });
  });
});
