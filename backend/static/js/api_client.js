/**
 * SmartCredit API client - JWT access/refresh handling
 */
(function() {
  'use strict';

  var ACCESS_KEY = 'smartcredit_access';
  var REFRESH_KEY = 'smartcredit_refresh';
  var API_BASE = '/api';

  function getAccessToken() {
    try {
      return localStorage.getItem(ACCESS_KEY);
    } catch (e) {
      return null;
    }
  }

  function getRefreshToken() {
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch (e) {
      return null;
    }
  }

  function setTokens(tokens) {
    if (!tokens || !tokens.access) return;
    try {
      localStorage.setItem(ACCESS_KEY, tokens.access);
      if (tokens.refresh) localStorage.setItem(REFRESH_KEY, tokens.refresh);
    } catch (e) {}
  }

  function clearTokens() {
    try {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch (e) {}
  }

  function refreshAccessToken() {
    var refresh = getRefreshToken();
    if (!refresh) return Promise.resolve(null);

    return fetch(API_BASE + '/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refresh }),
      credentials: 'same-origin'
    })
      .then(function(res) {
        return res.json().then(function(data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function(result) {
        if (!result.ok || !result.data || !result.data.access) {
          clearTokens();
          return null;
        }
        setTokens({ access: result.data.access, refresh: refresh });
        return result.data.access;
      })
      .catch(function() {
        clearTokens();
        return null;
      });
  }

  function authFetch(url, options) {
    var opts = Object.assign({}, options || {});
    var headers = Object.assign({}, opts.headers || {});
    var token = getAccessToken();
    if (token) headers.Authorization = 'Bearer ' + token;
    opts.headers = headers;
    if (!opts.credentials) opts.credentials = 'same-origin';

    return fetch(url, opts).then(function(res) {
      if (res.status !== 401) return res;
      return refreshAccessToken().then(function(newAccess) {
        if (!newAccess) return res;
        var retryOpts = Object.assign({}, opts);
        var retryHeaders = Object.assign({}, headers, { Authorization: 'Bearer ' + newAccess });
        retryOpts.headers = retryHeaders;
        return fetch(url, retryOpts);
      });
    });
  }

  window.SmartCreditApi = {
    getAccessToken: getAccessToken,
    getRefreshToken: getRefreshToken,
    setTokens: setTokens,
    clearTokens: clearTokens,
    refreshAccessToken: refreshAccessToken,
    authFetch: authFetch
  };
})();
