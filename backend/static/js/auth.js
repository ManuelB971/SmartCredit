/**
 * SmartCredit Auth - Login & Register pages
 */
(function() {
  'use strict';
  var API_BASE = '/api';

  function getCsrfHeaders() {
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value;
    var headers = { 'Content-Type': 'application/json' };
    if (csrfToken) headers['X-CSRFToken'] = csrfToken;
    return headers;
  }

  function extractError(data) {
    if (data.error) return data.error;
    if (data.detail) return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    if (typeof data === 'object') {
      var parts = [];
      for (var k in data) {
        if (Array.isArray(data[k])) parts.push(data[k].join(' '));
        else parts.push(String(data[k]));
      }
      if (parts.length) return parts.join('. ');
    }
    return 'Une erreur est survenue.';
  }

  function saveToken(data) {
    if (data.access) {
      try {
        localStorage.setItem('smartcredit_access', data.access);
        if (data.refresh) localStorage.setItem('smartcredit_refresh', data.refresh);
      } catch (e) {}
    }
  }

  function redirectAfterAuth() {
    var next = new URLSearchParams(window.location.search).get('next');
    window.location.href = next || '/';
  }

  document.addEventListener('DOMContentLoaded', function() {
    var formConnexion = document.getElementById('form-connexion');
    if (formConnexion) {
      formConnexion.addEventListener('submit', function(e) {
        e.preventDefault();
        var btn = document.getElementById('btn-login');
        var errEl = document.getElementById('login-error');
        btn.disabled = true;
        errEl.classList.add('hidden');
        fetch(API_BASE + '/auth/token/', {
          method: 'POST',
          headers: getCsrfHeaders(),
          body: JSON.stringify({
            email: document.getElementById('login-email').value.trim(),
            password: document.getElementById('login-password').value
          }),
          credentials: 'same-origin'  /* pour recevoir le cookie de session */
        })
          .then(function(res) { return res.json().then(function(d) { return { ok: res.ok, data: d }; }); })
          .then(function(r) {
            if (!r.ok) throw new Error(extractError(r.data));
            saveToken(r.data);
            redirectAfterAuth();
          })
          .catch(function(err) {
            errEl.textContent = err.message;
            errEl.classList.remove('hidden');
            btn.disabled = false;
          });
      });
    }

    var formInscription = document.getElementById('form-inscription');
    if (formInscription) {
      formInscription.addEventListener('submit', function(e) {
        e.preventDefault();
        var btn = document.getElementById('btn-inscription');
        var errEl = document.getElementById('inscription-error');
        btn.disabled = true;
        errEl.classList.add('hidden');
        var payload = {
          email: document.getElementById('insc-email').value.trim(),
          password: document.getElementById('insc-password').value,
          nom: document.getElementById('insc-nom').value.trim(),
          prenom: document.getElementById('insc-prenom').value.trim()
        };
        fetch(API_BASE + '/auth/register/', {
          method: 'POST',
          headers: getCsrfHeaders(),
          body: JSON.stringify(payload),
          credentials: 'same-origin'
        })
          .then(function(res) { return res.json().then(function(d) { return { ok: res.ok, data: d }; }); })
          .then(function(r) {
            if (!r.ok) throw new Error(extractError(r.data));
            saveToken(r.data);
            redirectAfterAuth();
          })
          .catch(function(err) {
            errEl.textContent = err.message;
            errEl.classList.remove('hidden');
            btn.disabled = false;
          });
      });
    }
  });
})();
