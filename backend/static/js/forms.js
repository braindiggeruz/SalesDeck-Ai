document.addEventListener('DOMContentLoaded', function() {
  function getUtmParams() {
    var params = new URLSearchParams(window.location.search);
    return {
      utm_source: params.get('utm_source') || '',
      utm_medium: params.get('utm_medium') || '',
      utm_campaign: params.get('utm_campaign') || '',
      utm_content: params.get('utm_content') || '',
      utm_term: params.get('utm_term') || '',
    };
  }

  var forms = document.querySelectorAll('form[data-enhanced]');
  forms.forEach(function(form) {
    var submitting = false;          // in-flight guard
    var alreadySucceeded = false;    // hard guard against double-Lead (manual resubmit after success)

    form.addEventListener('submit', function(e) {
      // Honeypot
      var hp = form.querySelector('input[name="website"]');
      if (hp && hp.value) {
        e.preventDefault();
        return;
      }
      e.preventDefault();

      if (submitting || alreadySucceeded) return;
      submitting = true;

      var submitBtn = form.querySelector('button[type="submit"]');
      var successEl = form.querySelector('[data-form-success]');
      var errorEl = form.querySelector('[data-form-error]');
      var originalText = submitBtn ? submitBtn.textContent : '';

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.setAttribute('aria-busy', 'true');
        submitBtn.textContent = '...';
      }
      if (successEl) successEl.classList.add('hidden');
      if (errorEl) errorEl.classList.add('hidden');

      var formData = new FormData(form);
      var data = {};
      formData.forEach(function(value, key) {
        if (key !== 'website') data[key] = value;
      });

      var utm = getUtmParams();
      Object.keys(utm).forEach(function(k) { data[k] = utm[k]; });
      data.page_url = window.location.href;
      data.referrer = document.referrer || '';

      fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(function(res) {
        if (!res.ok) throw new Error('Server error');
        return res.json();
      })
      .then(function(json) {
        alreadySucceeded = true;
        if (successEl) successEl.classList.remove('hidden');
        form.reset();
        if (typeof window.track === 'function') {
          window.track('lead_form_success', {
            source: data.source || 'contact_form',
            lead_type: data.lead_type || '',
            business_type: data.business || '',
            lead_id: (json && json.lead_id) || ''
          });
        }
        // Disable submit permanently after success to prevent duplicate Lead events
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.removeAttribute('aria-busy');
          submitBtn.textContent = originalText;
        }
      })
      .catch(function() {
        if (errorEl) errorEl.classList.remove('hidden');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.removeAttribute('aria-busy');
          submitBtn.textContent = originalText;
        }
      })
      .finally(function() {
        submitting = false;
      });
    });
  });
});
