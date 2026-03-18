-- SmartCredit (MVP1) - PostgreSQL schema
-- Source: Cahier des charges (sections 16.2 / 16.3) + durcissement MVP (banques, exports, consentements)

BEGIN;

-- ---------- ENUM types ----------
DO $$ BEGIN
  CREATE TYPE type_credit AS ENUM ('ETUDIANT', 'IMMOBILIER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE statut_simulation AS ENUM ('EN_COURS', 'TERMINEE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE scenario_resultat AS ENUM ('PRUDENT', 'EQUILIBRE', 'CONFORT');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE niveau_langage AS ENUM ('ETUDIANT', 'STANDARD', 'PROFESSIONNEL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE etat_export AS ENUM ('EN_ATTENTE', 'ENVOYE', 'ECHEC');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE type_consentement AS ENUM ('CONTACT', 'MARKETING');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ---------- Core tables ----------
CREATE TABLE IF NOT EXISTS utilisateurs (
  id BIGSERIAL PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  prenom VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  mot_de_passe_hash VARCHAR(255) NOT NULL,
  date_creation TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  date_derniere_connexion TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS simulations (
  id BIGSERIAL PRIMARY KEY,
  type_credit type_credit NOT NULL,
  date_simulation TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  statut statut_simulation NOT NULL DEFAULT 'EN_COURS',
  utilisateur_id BIGINT REFERENCES utilisateurs(id) ON DELETE SET NULL,
  source VARCHAR(30) NOT NULL DEFAULT 'web',
  ip_hash VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_simulations_utilisateur ON simulations(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_simulations_date ON simulations(date_simulation);
CREATE INDEX IF NOT EXISTS idx_simulations_type_credit ON simulations(type_credit);

-- ---------- 1:1 data captured for a simulation ----------
CREATE TABLE IF NOT EXISTS profils_financiers (
  id BIGSERIAL PRIMARY KEY,
  age INTEGER NOT NULL CHECK (age >= 18 AND age <= 100),
  situation_familiale VARCHAR(20) NOT NULL,
  nombre_enfants INTEGER NOT NULL DEFAULT 0 CHECK (nombre_enfants >= 0),
  ville VARCHAR(100),
  revenus_mensuels NUMERIC(10,2) NOT NULL CHECK (revenus_mensuels >= 0),
  autres_revenus NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (autres_revenus >= 0),
  charges_logement NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (charges_logement >= 0),
  charges_credits NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (charges_credits >= 0),
  autres_charges NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (autres_charges >= 0),
  type_contrat VARCHAR(20),
  anciennete_emploi_mois INTEGER CHECK (anciennete_emploi_mois IS NULL OR anciennete_emploi_mois >= 0),
  simulation_id BIGINT NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS projets_credit (
  id BIGSERIAL PRIMARY KEY,
  type_credit type_credit NOT NULL,
  montant_souhaite NUMERIC(12,2) NOT NULL CHECK (montant_souhaite > 0),
  duree_mois INTEGER NOT NULL CHECK (duree_mois > 0),
  apport_personnel NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (apport_personnel >= 0),
  simulation_id BIGINT NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE
);

-- ---------- Banks & offers (normalized) ----------
CREATE TABLE IF NOT EXISTS banques (
  id BIGSERIAL PRIMARY KEY,
  nom VARCHAR(150) NOT NULL UNIQUE,
  site_url TEXT
);

CREATE TABLE IF NOT EXISTS offres_bancaires (
  id BIGSERIAL PRIMARY KEY,
  banque_id BIGINT NOT NULL REFERENCES banques(id) ON DELETE RESTRICT,
  type_credit type_credit NOT NULL,
  duree_min_mois INTEGER NOT NULL CHECK (duree_min_mois > 0),
  duree_max_mois INTEGER NOT NULL CHECK (duree_max_mois > 0 AND duree_max_mois >= duree_min_mois),
  taux_annuel NUMERIC(5,3) NOT NULL CHECK (taux_annuel >= 0),
  conditions_particulieres TEXT,
  date_mise_a_jour DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_offres_type_credit ON offres_bancaires(type_credit);
CREATE INDEX IF NOT EXISTS idx_offres_banque_type ON offres_bancaires(banque_id, type_credit);
CREATE INDEX IF NOT EXISTS idx_offres_date_maj ON offres_bancaires(date_mise_a_jour);

-- ---------- Results & IA explanation ----------
CREATE TABLE IF NOT EXISTS resultats_simulations (
  id BIGSERIAL PRIMARY KEY,
  mensualite NUMERIC(10,2) NOT NULL CHECK (mensualite >= 0),
  taux_utilise NUMERIC(5,3) NOT NULL CHECK (taux_utilise >= 0),
  cout_total NUMERIC(12,2) NOT NULL CHECK (cout_total >= 0),
  taux_endettement NUMERIC(5,2) NOT NULL CHECK (taux_endettement >= 0),
  reste_a_vivre NUMERIC(10,2) CHECK (reste_a_vivre IS NULL OR reste_a_vivre >= 0),
  score_faisabilite INTEGER CHECK (score_faisabilite IS NULL OR (score_faisabilite >= 0 AND score_faisabilite <= 100)),
  scenario scenario_resultat,
  offre_bancaire_id BIGINT REFERENCES offres_bancaires(id) ON DELETE SET NULL,
  simulation_id BIGINT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
  date_calcul TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resultats_simulation ON resultats_simulations(simulation_id);
CREATE INDEX IF NOT EXISTS idx_resultats_offre ON resultats_simulations(offre_bancaire_id);

CREATE TABLE IF NOT EXISTS explications_ia (
  id BIGSERIAL PRIMARY KEY,
  texte_explication TEXT NOT NULL,
  recommandations TEXT,
  avertissements TEXT,
  niveau_langage niveau_langage NOT NULL DEFAULT 'STANDARD',
  simulation_id BIGINT NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE,
  date_generation TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------- UC4: PDF/email export tracking ----------
CREATE TABLE IF NOT EXISTS exports_pdf_email (
  id BIGSERIAL PRIMARY KEY,
  simulation_id BIGINT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
  email_destinataire VARCHAR(255) NOT NULL,
  etat etat_export NOT NULL DEFAULT 'EN_ATTENTE',
  date_demande TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  date_envoi TIMESTAMPTZ,
  erreur TEXT
);

CREATE INDEX IF NOT EXISTS idx_exports_simulation ON exports_pdf_email(simulation_id);
CREATE INDEX IF NOT EXISTS idx_exports_email ON exports_pdf_email(email_destinataire);

-- ---------- RGPD minimal: consent tracking ----------
CREATE TABLE IF NOT EXISTS consentements (
  id BIGSERIAL PRIMARY KEY,
  utilisateur_id BIGINT REFERENCES utilisateurs(id) ON DELETE SET NULL,
  email VARCHAR(255),
  type type_consentement NOT NULL,
  valeur BOOLEAN NOT NULL,
  date_consentement TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  source VARCHAR(30) NOT NULL DEFAULT 'web',
  CONSTRAINT consentements_identite_ck CHECK (utilisateur_id IS NOT NULL OR email IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_consentements_utilisateur ON consentements(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_consentements_email ON consentements(email);
CREATE INDEX IF NOT EXISTS idx_consentements_type ON consentements(type);

-- ---------- Helpful views (optional, read-only) ----------
-- Most recent completed simulations for a user (UC7)
CREATE OR REPLACE VIEW v_historique_simulations AS
SELECT
  s.id AS simulation_id,
  s.utilisateur_id,
  s.type_credit,
  s.date_simulation,
  s.statut,
  rs.id AS resultat_id,
  rs.scenario,
  rs.mensualite,
  rs.taux_utilise,
  rs.cout_total,
  rs.score_faisabilite,
  ob.id AS offre_id,
  b.nom AS banque_nom,
  ob.date_mise_a_jour AS offre_date_mise_a_jour
FROM simulations s
LEFT JOIN LATERAL (
  SELECT *
  FROM resultats_simulations r
  WHERE r.simulation_id = s.id
  ORDER BY r.date_calcul DESC
  LIMIT 1
) rs ON TRUE
LEFT JOIN offres_bancaires ob ON ob.id = rs.offre_bancaire_id
LEFT JOIN banques b ON b.id = ob.banque_id;

COMMIT;

