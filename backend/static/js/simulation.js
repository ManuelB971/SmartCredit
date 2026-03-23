/**
 * SmartCredit Simulation - Frontend logic for wizard + API
 */
(function() {
  'use strict';

  var STORAGE_KEY = 'smartcredit_wizard';
  var API_BASE = '/api';

  function getWizardData() {
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function setWizardData(data) {
    var current = getWizardData();
    var merged = Object.assign({}, current, data);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  }

  function formatNumber(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  function parseDecimal(val) {
    if (val === '' || val === null || val === undefined) return '0.00';
    var n = parseFloat(String(val).replace(/\s/g, '').replace(',', '.'));
    return isNaN(n) ? '0.00' : n.toFixed(2);
  }

  function formatDate(value) {
    if (!value) return '-';
    var d = new Date(value);
    if (isNaN(d.getTime())) return value;
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  var SmartCreditSimulation = {
    initEtape1: function() {
      var simId = parseInt(new URLSearchParams(window.location.search).get('simulation_id'), 10);
      var runInit = function() {
        var data = getWizardData();
        var type = new URLSearchParams(window.location.search).get('type') || data.type_credit || 'IMMOBILIER';
        setWizardData({ type_credit: type });

        // Pre-fill from storage
        if (data.age) document.getElementById('age').value = data.age;
      if (data.situation_familiale) {
        var radio = document.querySelector('input[name="family"][value="' + data.situation_familiale + '"]');
        if (radio) radio.checked = true;
      }
      if (data.nombre_enfants !== undefined) {
        document.getElementById('nombre_enfants').value = data.nombre_enfants;
        document.getElementById('enfants-value').textContent = data.nombre_enfants;
      }
      if (data.ville) document.getElementById('city').value = data.ville;

      var enfantsVal = parseInt(document.getElementById('nombre_enfants').value, 10) || 0;
      document.getElementById('btn-enfants-minus').addEventListener('click', function() {
        if (enfantsVal > 0) {
          enfantsVal--;
          document.getElementById('nombre_enfants').value = enfantsVal;
          document.getElementById('enfants-value').textContent = enfantsVal;
        }
      });
      document.getElementById('btn-enfants-plus').addEventListener('click', function() {
        enfantsVal++;
        document.getElementById('nombre_enfants').value = enfantsVal;
        document.getElementById('enfants-value').textContent = enfantsVal;
      });

      document.getElementById('form-etape1').addEventListener('submit', function(e) {
        e.preventDefault();
        var family = document.querySelector('input[name="family"]:checked');
        if (!family) {
          alert('Veuillez sélectionner votre situation familiale.');
          return;
        }
        setWizardData({
          age: parseInt(document.getElementById('age').value, 10),
          situation_familiale: family.value,
          nombre_enfants: parseInt(document.getElementById('nombre_enfants').value, 10) || 0,
          ville: document.getElementById('city').value.trim()
        });
        window.location.href = '/simulation/etape-2/';
      });
      };

      if (simId && !isNaN(simId)) {
        fetch(API_BASE + '/simulations/' + simId + '/')
          .then(function(res) { return res.ok ? res.json() : Promise.reject(); })
          .then(function(sim) {
            var pf = sim.profil_financier || {};
            var pc = sim.projet_credit || {};
            var sitFam = pf.situation_familiale;
            if (!sitFam || !['CELIBATAIRE','MARIE','PACS'].includes(sitFam)) sitFam = 'CELIBATAIRE';
            setWizardData({
              type_credit: sim.type_credit || 'IMMOBILIER',
              age: pf.age,
              situation_familiale: sitFam,
              nombre_enfants: pf.nombre_enfants,
              ville: pf.ville || '',
              type_contrat: pf.type_contrat || 'CDI',
              revenus_mensuels: String(pf.revenus_mensuels || '0'),
              autres_revenus: String(pf.autres_revenus || '0'),
              charges_logement: String(pf.charges_logement || '0'),
              charges_credits: String(pf.charges_credits || '0'),
              autres_charges: String(pf.autres_charges || '0'),
              anciennete_emploi_mois: pf.anciennete_emploi_mois || 0,
              montant_souhaite: String(pc.montant_souhaite || '0'),
              duree_mois: pc.duree_mois || 240,
              apport_personnel: String(pc.apport_personnel || '0')
            });
            runInit();
          })
          .catch(function() { runInit(); });
      } else {
        runInit();
      }
    },

    initEtape2: function() {
      var data = getWizardData();
      if (!data.type_credit) {
        window.location.href = '/simulation/etape-1/';
        return;
      }

      // Pre-fill
      if (data.type_contrat) {
        document.getElementById('type_contrat').value = data.type_contrat;
        document.querySelectorAll('.btn-contrat').forEach(function(btn) {
          btn.classList.remove('border-primary', 'text-primary');
          btn.classList.add('border-outline-variant/30', 'text-on-surface-variant');
          if (btn.dataset.value === data.type_contrat) {
            btn.classList.add('border-primary', 'text-primary');
            btn.classList.remove('border-outline-variant/30', 'text-on-surface-variant');
          }
        });
      }
      if (data.revenus_mensuels !== undefined) document.getElementById('salaire').value = data.revenus_mensuels;
      if (data.autres_revenus !== undefined) document.getElementById('autres').value = data.autres_revenus;
      if (data.charges_logement !== undefined) document.getElementById('loyer').value = data.charges_logement;
      if (data.charges_credits !== undefined) document.getElementById('credits').value = data.charges_credits;
      if (data.autres_charges !== undefined) document.getElementById('autres_charges').value = data.autres_charges;

      document.querySelectorAll('.btn-contrat').forEach(function(btn) {
        btn.addEventListener('click', function() {
          document.querySelectorAll('.btn-contrat').forEach(function(b) {
            b.classList.remove('border-primary', 'text-primary');
            b.classList.add('border-outline-variant/30', 'text-on-surface-variant');
          });
          btn.classList.add('border-primary', 'text-primary');
          btn.classList.remove('border-outline-variant/30', 'text-on-surface-variant');
          document.getElementById('type_contrat').value = btn.dataset.value;
          SmartCreditSimulation.updateResteAVivre();
        });
      });

      ['salaire', 'autres', 'loyer', 'credits', 'autres_charges'].forEach(function(id) {
        document.getElementById(id).addEventListener('input', SmartCreditSimulation.updateResteAVivre);
      });

      SmartCreditSimulation.updateResteAVivre();

      document.getElementById('btn-etape2-next').addEventListener('click', function() {
        var salaire = parseFloat(document.getElementById('salaire').value) || 0;
        if (salaire <= 0 && data.type_credit !== 'ETUDIANT') {
          var err = document.getElementById('error-message');
          if (err) {
            err.textContent = 'Veuillez saisir votre salaire net mensuel.';
            err.classList.remove('hidden');
            setTimeout(function() { err.classList.add('hidden'); }, 4000);
          }
          return;
        }
        setWizardData({
          type_contrat: document.getElementById('type_contrat').value,
          revenus_mensuels: parseDecimal(document.getElementById('salaire').value),
          autres_revenus: parseDecimal(document.getElementById('autres').value),
          charges_logement: parseDecimal(document.getElementById('loyer').value),
          charges_credits: parseDecimal(document.getElementById('credits').value),
          autres_charges: parseDecimal(document.getElementById('autres_charges').value)
        });
        window.location.href = '/simulation/etape-3/';
      });
    },

    updateResteAVivre: function() {
      var el = document.getElementById('reste-vivre-estime');
      if (!el) return;
      var salaire = parseFloat(document.getElementById('salaire').value) || 0;
      var autres = parseFloat(document.getElementById('autres').value) || 0;
      var loyer = parseFloat(document.getElementById('loyer').value) || 0;
      var credits = parseFloat(document.getElementById('credits').value) || 0;
      var autresCh = parseFloat(document.getElementById('autres_charges').value) || 0;
      var revenus = salaire + autres;
      var charges = loyer + credits + autresCh;
      var rav = revenus - charges;
      el.textContent = rav >= 0 ? formatNumber(Math.round(rav)) : '—';
    },

    initEtape3: function() {
      var data = getWizardData();
      if (!data.type_credit) {
        window.location.href = '/simulation/etape-1/';
        return;
      }

      var typeCredit = data.type_credit;
      document.getElementById('type_credit').value = typeCredit;

      var montantMin = typeCredit === 'ETUDIANT' ? 5000 : 50000;
      var montantMax = typeCredit === 'ETUDIANT' ? 50000 : 1000000;
      var montantDefault = typeCredit === 'ETUDIANT' ? 20000 : 245000;

      var montantInput = document.getElementById('montant');
      montantInput.min = montantMin;
      montantInput.max = montantMax;
      montantInput.step = typeCredit === 'ETUDIANT' ? 1000 : 5000;
      montantInput.value = data.montant_souhaite ? parseFloat(data.montant_souhaite) : montantDefault;

      var updateMontantDisplay = function() {
        var v = parseInt(montantInput.value, 10);
        document.getElementById('montant-display').textContent = formatNumber(v);
        document.getElementById('montant_raw').value = v;
      };
      montantInput.addEventListener('input', updateMontantDisplay);
      updateMontantDisplay();

      document.querySelectorAll('.btn-type-credit').forEach(function(btn) {
        btn.addEventListener('click', function() {
          typeCredit = btn.dataset.value;
          setWizardData({ type_credit: typeCredit });
          document.getElementById('type_credit').value = typeCredit;
          document.querySelectorAll('.btn-type-credit').forEach(function(b) {
            b.classList.remove('bg-surface-container-lowest', 'text-primary', 'shadow-sm');
            b.classList.add('text-on-surface-variant', 'bg-surface-container-high');
          });
          btn.classList.add('bg-surface-container-lowest', 'text-primary', 'shadow-sm');
          btn.classList.remove('text-on-surface-variant', 'bg-surface-container-high');
          if (typeCredit === 'ETUDIANT') {
            montantInput.min = 5000;
            montantInput.max = 50000;
            montantInput.step = 1000;
            montantInput.value = Math.min(20000, parseInt(montantInput.value, 10));
          } else {
            montantInput.min = 50000;
            montantInput.max = 1000000;
            montantInput.step = 5000;
          }
          updateMontantDisplay();
        });
        if (btn.dataset.value === typeCredit) {
          btn.classList.add('bg-surface-container-lowest', 'text-primary', 'shadow-sm');
          btn.classList.remove('text-on-surface-variant');
        }
      });

      var dureeMois = data.duree_mois ? parseInt(data.duree_mois, 10) : 240;
      document.getElementById('duree_mois').value = dureeMois;
      document.querySelectorAll('.btn-duree').forEach(function(btn) {
        var mois = parseInt(btn.dataset.mois, 10);
        btn.addEventListener('click', function() {
          dureeMois = mois;
          document.getElementById('duree_mois').value = dureeMois;
          document.querySelectorAll('.btn-duree').forEach(function(b) {
            b.classList.remove('border-primary', 'bg-surface-container-lowest');
            b.querySelector('span').classList.remove('text-primary');
            b.querySelector('span').classList.add('text-on-surface');
          });
          btn.classList.add('border-primary', 'bg-surface-container-lowest');
          btn.querySelector('span').classList.add('text-primary');
          btn.querySelector('span').classList.remove('text-on-surface');
        });
        if (mois === dureeMois) {
          btn.classList.add('border-primary', 'bg-surface-container-lowest');
          btn.querySelector('span').classList.add('text-primary');
        }
      });

      var apportInput = document.getElementById('apport');
      if (data.apport_personnel !== undefined) apportInput.value = String(data.apport_personnel).replace('.', '');
      apportInput.addEventListener('input', function() {
        this.value = this.value.replace(/[^\d]/g, '');
      });

      document.getElementById('btn-etape3-submit').addEventListener('click', function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = 'Envoi en cours...';

        var montant = parseFloat(document.getElementById('montant_raw').value) || parseFloat(document.getElementById('montant').value) || 245000;
        var apportVal = parseFloat(String(document.getElementById('apport').value).replace(/\s/g, '')) || 0;

        var payload = {
          type_credit: document.getElementById('type_credit').value,
          profil_financier: {
            age: data.age,
            situation_familiale: data.situation_familiale,
            nombre_enfants: data.nombre_enfants || 0,
            ville: data.ville || '',
            revenus_mensuels: data.revenus_mensuels || '0.00',
            autres_revenus: data.autres_revenus || '0.00',
            charges_logement: data.charges_logement || '0.00',
            charges_credits: data.charges_credits || '0.00',
            autres_charges: data.autres_charges || '0.00',
            type_contrat: data.type_contrat || 'CDI',
            anciennete_emploi_mois: data.anciennete_emploi_mois || 0
          },
          projet_credit: {
            type_credit: document.getElementById('type_credit').value,
            montant_souhaite: montant.toFixed(2),
            duree_mois: parseInt(document.getElementById('duree_mois').value, 10),
            apport_personnel: apportVal.toFixed(2)
          }
        };

        fetch(API_BASE + '/simulations/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
          .then(function(res) {
            if (!res.ok) return res.json().then(function(j) { throw new Error(j.detail || j.error || JSON.stringify(j)); });
            return res.json();
          })
          .then(function(json) {
            sessionStorage.removeItem(STORAGE_KEY);
            window.location.href = '/simulation/analyse/' + json.simulation_id + '/';
          })
          .catch(function(err) {
            btn.disabled = false;
            btn.innerHTML = '<span class="font-[\'Inter\'] text-sm font-medium uppercase tracking-wider">Lancer l\'analyse</span><span class="material-symbols-outlined ml-2">arrow_forward</span>';
            var errEl = document.getElementById('error-message');
            if (errEl) {
              errEl.textContent = err.message || 'Erreur lors de la création de la simulation.';
              errEl.classList.remove('hidden');
              setTimeout(function() { errEl.classList.add('hidden'); }, 6000);
            }
          });
      });
    },

    initAnalyse: function(simulationId) {
      if (!simulationId) {
        window.location.href = '/';
        return;
      }

      var progress = 0;
      var iv = setInterval(function() {
        progress = Math.min(progress + 5, 90);
        var bar = document.getElementById('progress-bar');
        var pct = document.getElementById('progress-pct');
        if (bar) bar.style.width = progress + '%';
        if (pct) pct.textContent = progress + '%';
      }, 300);

      fetch(API_BASE + '/simulations/' + simulationId + '/calcul/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      })
        .then(function(res) {
          clearInterval(iv);
          var bar = document.getElementById('progress-bar');
          var pct = document.getElementById('progress-pct');
          if (bar) bar.style.width = '100%';
          if (pct) pct.textContent = '100%';
          if (!res.ok) return res.json().then(function(j) { throw new Error(j.error || JSON.stringify(j)); });
          return res.json();
        })
        .then(function() {
          window.location.href = '/simulation/resultats/' + simulationId + '/';
        })
        .catch(function(err) {
          clearInterval(iv);
          document.getElementById('task-active').classList.add('hidden');
          document.getElementById('error-container').classList.remove('hidden');
          document.getElementById('error-container').querySelector('p').textContent = (err.message || 'Une erreur s\'est produite.') + ' Vous pouvez recommencer.';
        });
    },

    initTableauBord: function(simulationId) {
      if (!simulationId) {
        window.location.href = '/';
        return;
      }

      fetch(API_BASE + '/simulations/' + simulationId + '/')
        .then(function(res) {
          if (!res.ok) throw new Error('Simulation introuvable');
          return res.json();
        })
        .then(function(sim) {
          document.getElementById('loading-state').classList.add('hidden');
          document.getElementById('results-state').classList.remove('hidden');

          var resultats = sim.resultats || [];
          var best = resultats[0];
          for (var i = 0; i < resultats.length; i++) {
            if (resultats[i].offre_bancaire && (!best || !best.offre_bancaire || parseFloat(resultats[i].offre_bancaire.taux_annuel) < parseFloat(best.offre_bancaire.taux_annuel))) {
              best = resultats[i];
            }
          }
          if (best && best.offre_bancaire) {
            document.getElementById('best-taux').textContent = parseFloat(best.offre_bancaire.taux_annuel).toFixed(2).replace('.', ',') + ' %';
            document.getElementById('best-banque').textContent = 'chez ' + best.offre_bancaire.banque.nom;
          }

          var scenarioLabels = { PRUDENT: 'Prudent', EQUILIBRE: 'Équilibré', CONFORT: 'Confort' };
          var scenarioDescs = { PRUDENT: 'Remboursement accéléré', EQUILIBRE: 'Le meilleur compromis', CONFORT: 'Souplesse maximale' };
          var scenarioIcons = { PRUDENT: 'timer', EQUILIBRE: 'balance', CONFORT: 'spa' };

          var order = ['PRUDENT', 'EQUILIBRE', 'CONFORT'];
          var container = document.getElementById('scenarios-container');
          container.innerHTML = '';
          order.forEach(function(scenarioKey) {
            var r = resultats.find(function(x) { return x.scenario === scenarioKey; });
            if (!r) return;
            var isReco = scenarioKey === 'EQUILIBRE';
            var html = '<div class="bg-surface-container-low hover:bg-surface-container-lowest transition-colors p-6 rounded-xl border ' + (isReco ? 'border-2 border-primary relative bg-surface-container-lowest shadow-[0_12px_48px_rgba(0,101,84,0.12)]' : 'border-transparent hover:border-outline-variant/20') + ' group">';
            if (isReco) html += '<div class="absolute -top-3 right-6 bg-primary text-white px-4 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-lg"><span class="material-symbols-outlined text-xs" style="font-variation-settings: \'FILL\' 1;">star</span>RECOMMANDÉ</div>';
            html += '<div class="flex justify-between items-start mb-6"><div><h4 class="' + (isReco ? 'text-xl font-bold text-primary' : 'text-lg font-bold') + '">Scénario ' + scenarioLabels[scenarioKey] + '</h4><p class="text-sm text-on-surface-variant">' + scenarioDescs[scenarioKey] + '</p></div><span class="material-symbols-outlined ' + (isReco ? 'text-primary text-3xl' : 'text-on-surface-variant group-hover:text-primary transition-colors') + '">' + scenarioIcons[scenarioKey] + '</span></div>';
            html += '<div class="grid grid-cols-2 gap-8"><div><p class="text-xs font-bold uppercase text-on-surface-variant tracking-wider mb-1">Mensualité</p><p class="' + (isReco ? 'text-3xl' : 'text-2xl') + ' font-headline font-extrabold text-on-surface">' + formatNumber(parseFloat(r.mensualite).toFixed(0)) + ' €</p></div><div><p class="text-xs font-bold uppercase text-on-surface-variant tracking-wider mb-1">Coût Total</p><p class="' + (isReco ? 'text-3xl' : 'text-2xl') + ' font-headline font-extrabold text-on-surface">' + formatNumber(parseFloat(r.cout_total).toFixed(0)) + ' €</p></div></div></div>';
            container.insertAdjacentHTML('beforeend', html);
          });

          var score = (best && best.score_faisabilite !== null && best.score_faisabilite !== undefined) ? best.score_faisabilite : 75;
          document.getElementById('score-value').textContent = score;
          var circumference = 264;
          var offset = circumference - (score / 100) * circumference;
          document.getElementById('score-circle').style.strokeDashoffset = offset;
          document.getElementById('score-label').innerHTML = score >= 70 ? '<span class="material-symbols-outlined text-lg" style="font-variation-settings: \'FILL\' 1;">check_circle</span>Dossier solide' : '<span class="material-symbols-outlined text-lg">info</span>Dossier à consolider';

          var ai = sim.explication_ia;
          var explEl = document.getElementById('ai-explanation');
          if (ai && ai.texte_explication) {
            explEl.innerHTML = '<p>' + ai.texte_explication.replace(/\n/g, '</p><p>') + '</p>';
            if (ai.recommandations) explEl.innerHTML += '<div class="p-4 bg-surface-container-low rounded-lg border-l-4 border-primary italic text-sm">' + ai.recommandations + '</div>';
          } else {
            explEl.innerHTML = '<p>Analyse terminée. Consultez les scénarios ci-contre.</p>';
          }

          document.body.setAttribute('data-simulation-id', simulationId);
          var btnModif = document.getElementById('btn-modifier-sim');
          if (btnModif) btnModif.setAttribute('href', '/simulation/etape-1/?simulation_id=' + simulationId);

          document.getElementById('btn-email').addEventListener('click', function() {
            document.getElementById('email-modal').classList.remove('hidden');
          });
          document.getElementById('email-modal-close').addEventListener('click', function() {
            document.getElementById('email-modal').classList.add('hidden');
          });
          var registerBtn = document.getElementById('btn-register');
          var registerIcon = document.getElementById('btn-register-icon');
          var registerLabel = document.getElementById('btn-register-label');
          var isLoggedIn = false;
          if (window.SmartCreditApi && window.SmartCreditApi.getAccessToken) {
            isLoggedIn = !!window.SmartCreditApi.getAccessToken();
          }

          if (registerBtn && isLoggedIn) {
            if (registerIcon) registerIcon.textContent = 'save';
            if (registerLabel) registerLabel.textContent = 'Sauvegarder';
          }

          document.getElementById('btn-register').addEventListener('click', function() {
            if (isLoggedIn && window.SmartCreditApi && window.SmartCreditApi.authFetch) {
              registerBtn.disabled = true;
              window.SmartCreditApi.authFetch(API_BASE + '/simulations/' + simulationId + '/save/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
              })
                .then(function(res) {
                  if (!res.ok) return res.json().then(function(j) { throw new Error(j.error || 'Erreur de sauvegarde'); });
                  if (registerIcon) registerIcon.textContent = 'check_circle';
                  if (registerLabel) registerLabel.textContent = 'Simulation sauvegardee';
                  registerBtn.classList.remove('border-primary', 'text-primary', 'hover:bg-primary/5');
                  registerBtn.classList.add('bg-primary', 'text-white');
                })
                .catch(function(err) {
                  document.getElementById('error-container').classList.remove('hidden');
                  document.getElementById('error-container').querySelector('p').textContent = err.message || 'Erreur de sauvegarde.';
                  registerBtn.disabled = false;
                });
              return;
            }
            document.getElementById('register-modal').classList.remove('hidden');
          });
          document.getElementById('register-modal-close').addEventListener('click', function() {
            document.getElementById('register-modal').classList.add('hidden');
          });
          document.getElementById('form-export-email').addEventListener('submit', function(e) {
            e.preventDefault();
            var email = document.getElementById('email-dest').value.trim();
            if (!email) return;
            var submitBtn = document.getElementById('btn-submit-email');
            submitBtn.disabled = true;
            document.getElementById('email-error').classList.add('hidden');
            fetch(API_BASE + '/simulations/' + simulationId + '/export-email/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: email })
            })
              .then(function(res) {
                if (!res.ok) return res.json().then(function(j) { throw new Error(j.email || j.detail || 'Erreur'); });
                document.getElementById('email-success').classList.remove('hidden');
                setTimeout(function() {
                  document.getElementById('email-modal').classList.add('hidden');
                  document.getElementById('email-success').classList.add('hidden');
                  submitBtn.disabled = false;
                }, 2000);
              })
              .catch(function(err) {
                document.getElementById('email-error').textContent = err.message;
                document.getElementById('email-error').classList.remove('hidden');
                submitBtn.disabled = false;
              });
          });
          document.getElementById('form-register').addEventListener('submit', function(e) {
            e.preventDefault();
            var payload = {
              email: document.getElementById('reg-email').value.trim(),
              password: document.getElementById('reg-password').value,
              nom: document.getElementById('reg-nom').value.trim(),
              prenom: document.getElementById('reg-prenom').value.trim()
            };
            if (simulationId && !isNaN(simulationId)) payload.simulation_id = simulationId;
            var submitBtn = document.getElementById('btn-submit-register');
            submitBtn.disabled = true;
            document.getElementById('register-error').classList.add('hidden');
            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value;
            var headers = { 'Content-Type': 'application/json' };
            if (csrfToken) headers['X-CSRFToken'] = csrfToken;
            fetch(API_BASE + '/auth/register/', {
              method: 'POST',
              headers: headers,
              body: JSON.stringify(payload),
              credentials: 'same-origin'
            })
              .then(function(res) {
                return res.json().then(function(data) {
                  if (!res.ok) {
                    var msg = data.error || data.detail;
                    if (!msg && typeof data === 'object') {
                      var parts = [];
                      for (var k in data) {
                        if (Array.isArray(data[k])) parts.push(data[k].join(' '));
                        else parts.push(String(data[k]));
                      }
                      msg = parts.length ? parts.join('. ') : 'Erreur lors de l\'inscription';
                    }
                    throw new Error(msg || 'Erreur lors de l\'inscription');
                  }
                  return data;
                });
              })
              .then(function() {
                document.getElementById('register-success').classList.remove('hidden');
                setTimeout(function() {
                  document.getElementById('register-modal').classList.add('hidden');
                  document.getElementById('register-success').classList.add('hidden');
                  submitBtn.disabled = false;
                }, 2500);
              })
              .catch(function(err) {
                document.getElementById('register-error').textContent = err.message;
                document.getElementById('register-error').classList.remove('hidden');
                submitBtn.disabled = false;
              });
          });
        })
        .catch(function() {
          document.getElementById('loading-state').innerHTML = '<p class="text-error">Simulation introuvable.</p><a href="/simulation/etape-1/" class="text-primary underline">Recommencer</a>';
        });
    },

    initHistorique: function() {
      var loadingEl = document.getElementById('history-loading');
      var emptyEl = document.getElementById('history-empty');
      var errorEl = document.getElementById('history-error');
      var listEl = document.getElementById('history-list');

      if (!window.SmartCreditApi || !window.SmartCreditApi.authFetch) {
        loadingEl.classList.add('hidden');
        errorEl.classList.remove('hidden');
        errorEl.textContent = 'Session indisponible. Reconnectez-vous.';
        return;
      }

      window.SmartCreditApi.authFetch(API_BASE + '/users/me/simulations/', { method: 'GET' })
        .then(function(res) {
          if (res.status === 401) {
            window.location.href = '/connexion/?next=/simulation/historique/';
            return null;
          }
          if (!res.ok) {
            return res.json().then(function(j) { throw new Error(j.error || 'Impossible de charger votre historique.'); });
          }
          return res.json();
        })
        .then(function(payload) {
          if (!payload) return;
          var sims = payload.simulations || [];
          loadingEl.classList.add('hidden');
          if (!sims.length) {
            emptyEl.classList.remove('hidden');
            return;
          }

          listEl.classList.remove('hidden');
          listEl.innerHTML = sims.map(function(sim) {
            var typeLabel = sim.type_credit === 'IMMOBILIER' ? 'Immobilier' : 'Etudiant';
            return (
              '<a href="/simulation/resultats/' + sim.id + '/" class="block bg-surface-container-low rounded-xl p-5 border border-outline-variant/20 hover:bg-surface-container-lowest transition-colors">' +
                '<div class="flex items-center justify-between gap-4">' +
                  '<div>' +
                    '<p class="text-xs uppercase tracking-widest text-on-surface-variant">Simulation #' + sim.id + '</p>' +
                    '<p class="text-lg font-semibold text-on-surface mt-1">' + typeLabel + '</p>' +
                  '</div>' +
                  '<div class="text-right">' +
                    '<p class="text-sm text-on-surface-variant">' + formatDate(sim.date_simulation) + '</p>' +
                    '<p class="text-xs text-on-surface-variant mt-1">' + (sim.statut || '-') + '</p>' +
                  '</div>' +
                '</div>' +
              '</a>'
            );
          }).join('');
        })
        .catch(function(err) {
          loadingEl.classList.add('hidden');
          errorEl.classList.remove('hidden');
          errorEl.textContent = err.message || 'Impossible de charger votre historique.';
        });
    }
  };

  window.SmartCreditSimulation = SmartCreditSimulation;
})();
