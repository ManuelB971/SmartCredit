/**
 * SmartCredit header auth state (guest/profile menu)
 */
(function() {
  'use strict';

  function setVisible(el, visible) {
    if (!el) return;
    if (visible) el.classList.remove('hidden');
    else el.classList.add('hidden');
  }

  function closeMenu() {
    var menu = document.getElementById('header-auth-menu');
    var btn = document.getElementById('header-auth-toggle');
    if (!menu || !btn) return;
    menu.classList.add('hidden');
    btn.setAttribute('aria-expanded', 'false');
  }

  function openMenu() {
    var menu = document.getElementById('header-auth-menu');
    var btn = document.getElementById('header-auth-toggle');
    if (!menu || !btn) return;
    menu.classList.remove('hidden');
    btn.setAttribute('aria-expanded', 'true');
  }

  function wireMenuInteractions() {
    var btn = document.getElementById('header-auth-toggle');
    var menu = document.getElementById('header-auth-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', function() {
      if (menu.classList.contains('hidden')) openMenu();
      else closeMenu();
    });

    document.addEventListener('click', function(e) {
      if (!menu.contains(e.target) && !btn.contains(e.target)) closeMenu();
    });
  }

  function initHeaderAuth() {
    var guestActions = document.getElementById('header-guest-actions');
    var userActions = document.getElementById('header-user-actions');
    var emailEl = document.getElementById('header-user-email');
    var logoutBtn = document.getElementById('header-logout-btn');
    var deleteBtn = document.getElementById('header-delete-btn');

    if (!window.SmartCreditApi) return;

    setVisible(guestActions, true);
    setVisible(userActions, false);

    window.SmartCreditApi.authFetch('/api/auth/me/', { method: 'GET' })
      .then(function(res) {
        if (!res.ok) throw new Error('not-authenticated');
        return res.json();
      })
      .then(function(me) {
        if (emailEl) emailEl.textContent = me.email || 'Mon profil';
        setVisible(guestActions, false);
        setVisible(userActions, true);
        wireMenuInteractions();
      })
      .catch(function() {
        setVisible(guestActions, true);
        setVisible(userActions, false);
      });

    if (logoutBtn) {
      logoutBtn.addEventListener('click', function() {
        window.SmartCreditApi.clearTokens();
        closeMenu();
        window.location.href = '/';
      });
    }

    if (deleteBtn) {
      deleteBtn.addEventListener('click', function() {
        var ok = window.confirm('Voulez-vous vraiment supprimer votre compte ? Cette action est definitive.');
        if (!ok) return;

        deleteBtn.disabled = true;
        window.SmartCreditApi.authFetch('/api/auth/me/', { method: 'DELETE' })
          .then(function() {
            window.SmartCreditApi.clearTokens();
            closeMenu();
            window.location.href = '/';
          })
          .catch(function() {
            deleteBtn.disabled = false;
            window.alert('Impossible de supprimer le compte pour le moment.');
          });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', initHeaderAuth);
})();
