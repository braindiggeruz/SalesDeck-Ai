document.addEventListener('DOMContentLoaded', function() {
  var forms = document.querySelectorAll('form[data-enhanced]');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      // Check honeypot
      var hp = form.querySelector('input[name="website"]');
      if (hp && hp.value) {
        e.preventDefault();
        return;
      }

      // Progressive: if JS works, use fetch; otherwise fallback to normal submit
      e.preventDefault();

      var submitBtn = form.querySelector('button[type="submit"]');
      var successEl = form.querySelector('[data-form-success]');
      var errorEl = form.querySelector('[data-form-error]');
      var originalText = submitBtn ? submitBtn.textContent : '';

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '...';
      }
      if (successEl) successEl.classList.add('hidden');
      if (errorEl) errorEl.classList.add('hidden');

      var formData = new FormData(form);
      var data = {};
      formData.forEach(function(value, key) {
        if (key !== 'website') data[key] = value;
      });

      fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(function(res) {
        if (!res.ok) throw new Error('Server error');
        return res.json();
      })
      .then(function() {
        if (successEl) successEl.classList.remove('hidden');
        form.reset();
        if (typeof track === 'function') track('lead', { source: 'contact_form' });
      })
      .catch(function() {
        if (errorEl) errorEl.classList.remove('hidden');
      })
      .finally(function() {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      });
    });
  });
});
