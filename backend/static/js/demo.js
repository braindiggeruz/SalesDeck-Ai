/* Demo: interactive scenario picker with mock chat */
(function() {
  var dataEl = document.getElementById('demo-scenarios-data');
  var stringsEl = document.getElementById('demo-strings-data');
  var msgEl = document.getElementById('demo-messages');
  var statusEl = document.getElementById('demo-status');
  var finalEl = document.getElementById('demo-final');
  var replayBtn = document.getElementById('demo-replay');
  var btns = document.querySelectorAll('[data-demo-scenario]');

  if (!dataEl || !msgEl) return;

  var scenarios, strings;
  try {
    scenarios = JSON.parse(dataEl.textContent);
    strings = JSON.parse((stringsEl && stringsEl.textContent) || '{}');
  } catch (e) { return; }

  var currentTimers = [];
  var currentId = scenarios[0] && scenarios[0].id;

  function clearTimers() {
    currentTimers.forEach(function(t) { clearTimeout(t); });
    currentTimers = [];
  }

  function track(name, payload) {
    if (typeof window.track === 'function') window.track(name, payload || {});
  }

  function bubble(msg) {
    var wrap = document.createElement('div');
    wrap.className = 'flex ' + (msg.role === 'user' ? 'justify-end' : 'justify-start');
    var b = document.createElement('div');
    var base = 'max-w-[85%] px-3.5 py-2 rounded-2xl text-sm leading-relaxed transition-opacity duration-200 opacity-0';
    var theme = msg.role === 'user'
      ? ' bg-brand-accent text-white rounded-br-md'
      : ' bg-brand-bg border border-brand-border text-neutral-200 rounded-bl-md';
    b.className = base + theme;
    b.textContent = msg.text;
    wrap.appendChild(b);
    msgEl.appendChild(wrap);
    requestAnimationFrame(function() { b.classList.remove('opacity-0'); });
    msgEl.scrollTop = msgEl.scrollHeight;
  }

  function typingIndicator() {
    var wrap = document.createElement('div');
    wrap.className = 'flex justify-start typing-indicator';
    wrap.innerHTML = '<div class="px-3.5 py-2.5 rounded-2xl bg-brand-bg border border-brand-border rounded-bl-md text-neutral-500 text-xs">···</div>';
    msgEl.appendChild(wrap);
    msgEl.scrollTop = msgEl.scrollHeight;
    return wrap;
  }

  function setStatus(text, theme) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.className = 'text-[10px] font-semibold px-2 py-1 rounded-full ' + (theme || 'text-brand-accent-light bg-brand-accent/10');
  }

  function play(scenarioId) {
    var sc = scenarios.find(function(s) { return s.id === scenarioId; });
    if (!sc) return;
    currentId = scenarioId;
    clearTimers();
    msgEl.innerHTML = '';
    setStatus(strings['new'] || 'New', 'text-brand-accent-light bg-brand-accent/10');
    if (finalEl) { finalEl.textContent = ''; finalEl.style.opacity = 0; }

    track('demo_start', { scenario: scenarioId });

    var delay = 350;
    sc.messages.forEach(function(m, i) {
      // typing dot for bot only
      if (m.role === 'bot') {
        currentTimers.push(setTimeout(function() {
          var t = typingIndicator();
          currentTimers.push(setTimeout(function() {
            t.remove();
            bubble(m);
            if (i === Math.floor(sc.messages.length / 2)) {
              setStatus(strings['qualified'] || 'Qualified', 'text-emerald-400 bg-emerald-500/10');
            }
          }, 700));
        }, delay));
        delay += 1500;
      } else {
        currentTimers.push(setTimeout(function() { bubble(m); }, delay));
        delay += 900;
      }
    });

    // Final state
    currentTimers.push(setTimeout(function() {
      setStatus(sc.status_final, 'text-white bg-brand-accent border border-brand-accent/30');
      if (finalEl) {
        finalEl.textContent = '✓ ' + sc.status_final;
        finalEl.style.opacity = 1;
      }
    }, delay + 300));
  }

  function setActive(id) {
    btns.forEach(function(b) {
      var active = b.getAttribute('data-demo-scenario') === id;
      b.setAttribute('aria-selected', active ? 'true' : 'false');
      if (active) {
        b.classList.remove('bg-brand-card', 'border-brand-border', 'text-neutral-400');
        b.classList.add('bg-brand-accent/10', 'border-brand-accent/40', 'text-white');
      } else {
        b.classList.add('bg-brand-card', 'border-brand-border', 'text-neutral-400');
        b.classList.remove('bg-brand-accent/10', 'border-brand-accent/40', 'text-white');
      }
    });
  }

  btns.forEach(function(b) {
    b.addEventListener('click', function() {
      var id = b.getAttribute('data-demo-scenario');
      setActive(id);
      play(id);
    });
  });

  if (replayBtn) {
    replayBtn.addEventListener('click', function() {
      track('demo_replay', { scenario: currentId });
      play(currentId);
    });
  }

  // Auto-play first scenario after small delay
  if (currentId) {
    setTimeout(function() { play(currentId); }, 400);
  }
})();
