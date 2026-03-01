// Smart Crédit - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Smart Crédit initialized');

    // API base URL
    const API_BASE_URL = '/api/simulation/';

    // Handle wizard forms
    const step1Form = document.getElementById('step1-form');
    if (step1Form) {
        step1Form.addEventListener('submit', handleStep1);
    }

    const step2Form = document.getElementById('step2-form');
    if (step2Form) {
        step2Form.addEventListener('submit', handleStep2);
    }

    const step3Form = document.getElementById('step3-form');
    if (step3Form) {
        step3Form.addEventListener('submit', handleStep3);
    }

    function handleStep1(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        sessionStorage.setItem('step1', JSON.stringify(Object.fromEntries(formData)));
        window.location.href = '/wizard/step2/';
    }

    function handleStep2(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        sessionStorage.setItem('step2', JSON.stringify(Object.fromEntries(formData)));
        window.location.href = '/wizard/step3/';
    }

    async function handleStep3(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const step3Data = Object.fromEntries(formData);

        const step1 = JSON.parse(sessionStorage.getItem('step1') || '{}');
        const step2 = JSON.parse(sessionStorage.getItem('step2') || '{}');

        const payload = {
            type_credit: new URLSearchParams(window.location.search).get('type') || 'IMMOBILIER',
            profil_financier: {
                age: parseInt(step1.age),
                situation_familiale: step1.situation_familiale,
                ville: step1.ville,
                revenus_mensuels: parseFloat(step2.revenus_mensuels),
                charges_logement: parseFloat(step2.charges_logement),
                charges_credits: parseFloat(step2.charges_credits),
                charges_autres: parseFloat(step2.charges_autres || 0),
                type_contrat: step2.type_contrat,
                anciennete_emploi_mois: parseInt(step2.anciennete_emploi_mois)
            },
            projet_credit: {
                montant_souhaite: parseFloat(step3Data.montant_souhaite),
                duree_mois: parseInt(step3Data.duree_mois),
                apport_personnel: parseFloat(step3Data.apport_personnel)
            }
        };

        try {
            const response = await fetch(API_BASE_URL + 'simulations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Creation failed');

            const data = await response.json();
            sessionStorage.setItem('simulationId', data.id);

            // Run calculation
            window.location.href = '/wizard/loading/';

            // After 2s, run calculation
            setTimeout(() => {
                runCalculation(data.id);
            }, 2000);

        } catch (error) {
            console.error('Error:', error);
            alert('Erreur lors de la création de la simulation');
        }
    }

    async function runCalculation(simulationId) {
        try {
            const response = await fetch(API_BASE_URL + 'simulations/' + simulationId + '/calcul/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error('Calculation failed');

            window.location.href = '/results/' + simulationId + '/';

        } catch (error) {
            console.error('Calculation error:', error);
            alert('Erreur lors du calcul');
        }
    }

    // Handle email sending
    const emailButtons = document.querySelectorAll('[data-email-send]');
    emailButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const email = prompt('Votre email?');
            if (!email) return;

            const simulationId = new URLSearchParams(window.location.search).get('id');

            try {
                const response = await fetch('/api/notifications/send_email/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        simulation_id: simulationId,
                        email: email
                    })
                });

                if (response.ok) {
                    alert('Email envoyé avec succès!');
                } else {
                    alert('Erreur lors de l\'envoi de l\'email');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
});

// Utility function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch('/api/simulation/' + endpoint, options);
    return response.json();
}
