from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Banque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=150, unique=True)),
                ("site_url", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Simulation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type_credit", models.CharField(choices=[("ETUDIANT", "Etudiant"), ("IMMOBILIER", "Immobilier")], max_length=20)),
                ("date_simulation", models.DateTimeField(auto_now_add=True)),
                ("statut", models.CharField(choices=[("EN_COURS", "En cours"), ("TERMINEE", "Terminee")], default="EN_COURS", max_length=20)),
                ("source", models.CharField(default="web", max_length=30)),
                ("ip_hash", models.CharField(blank=True, max_length=255, null=True)),
                ("utilisateur", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="simulations", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="OffreBancaire",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type_credit", models.CharField(choices=[("ETUDIANT", "Etudiant"), ("IMMOBILIER", "Immobilier")], max_length=20)),
                ("duree_min_mois", models.PositiveIntegerField()),
                ("duree_max_mois", models.PositiveIntegerField()),
                ("taux_annuel", models.DecimalField(decimal_places=3, max_digits=5)),
                ("conditions_particulieres", models.TextField(blank=True, null=True)),
                ("date_mise_a_jour", models.DateField()),
                ("banque", models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name="offres", to="credit.banque")),
            ],
        ),
        migrations.CreateModel(
            name="ProfilFinancier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("age", models.PositiveIntegerField()),
                ("situation_familiale", models.CharField(max_length=20)),
                ("nombre_enfants", models.PositiveIntegerField(default=0)),
                ("ville", models.CharField(blank=True, max_length=100, null=True)),
                ("revenus_mensuels", models.DecimalField(decimal_places=2, max_digits=10)),
                ("autres_revenus", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("charges_logement", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("charges_credits", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("autres_charges", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("type_contrat", models.CharField(blank=True, max_length=20, null=True)),
                ("anciennete_emploi_mois", models.PositiveIntegerField(blank=True, null=True)),
                ("simulation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profil_financier", to="credit.simulation")),
            ],
        ),
        migrations.CreateModel(
            name="ProjetCredit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type_credit", models.CharField(choices=[("ETUDIANT", "Etudiant"), ("IMMOBILIER", "Immobilier")], max_length=20)),
                ("montant_souhaite", models.DecimalField(decimal_places=2, max_digits=12)),
                ("duree_mois", models.PositiveIntegerField()),
                ("apport_personnel", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("simulation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="projet_credit", to="credit.simulation")),
            ],
        ),
        migrations.CreateModel(
            name="ResultatSimulation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mensualite", models.DecimalField(decimal_places=2, max_digits=10)),
                ("taux_utilise", models.DecimalField(decimal_places=3, max_digits=5)),
                ("cout_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("taux_endettement", models.DecimalField(decimal_places=2, max_digits=5)),
                ("reste_a_vivre", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("score_faisabilite", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("scenario", models.CharField(blank=True, choices=[("PRUDENT", "Prudent"), ("EQUILIBRE", "Equilibre"), ("CONFORT", "Confort")], max_length=20, null=True)),
                ("date_calcul", models.DateTimeField(auto_now_add=True)),
                ("offre_bancaire", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="credit.offrebancaire")),
                ("simulation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resultats", to="credit.simulation")),
            ],
        ),
        migrations.CreateModel(
            name="ExplicationIA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texte_explication", models.TextField()),
                ("recommandations", models.TextField(blank=True, null=True)),
                ("avertissements", models.TextField(blank=True, null=True)),
                ("niveau_langage", models.CharField(choices=[("ETUDIANT", "Etudiant"), ("STANDARD", "Standard"), ("PROFESSIONNEL", "Professionnel")], default="STANDARD", max_length=20)),
                ("date_generation", models.DateTimeField(auto_now_add=True)),
                ("simulation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="explication_ia", to="credit.simulation")),
            ],
        ),
        migrations.AddIndex(
            model_name="simulation",
            index=models.Index(fields=["utilisateur"], name="credit_sim_utilisa_2d4d60_idx"),
        ),
        migrations.AddIndex(
            model_name="simulation",
            index=models.Index(fields=["date_simulation"], name="credit_sim_date_si_9063ff_idx"),
        ),
        migrations.AddIndex(
            model_name="simulation",
            index=models.Index(fields=["type_credit"], name="credit_sim_type_cr_ba7d18_idx"),
        ),
        migrations.AddIndex(
            model_name="offrebancaire",
            index=models.Index(fields=["type_credit"], name="credit_off_type_cr_1a3cf8_idx"),
        ),
        migrations.AddIndex(
            model_name="offrebancaire",
            index=models.Index(fields=["banque", "type_credit"], name="credit_off_banque__66cf50_idx"),
        ),
        migrations.AddIndex(
            model_name="offrebancaire",
            index=models.Index(fields=["date_mise_a_jour"], name="credit_off_date_mi_1a3b6e_idx"),
        ),
        migrations.AddIndex(
            model_name="resultatsimulation",
            index=models.Index(fields=["simulation"], name="credit_res_simulat_2b8c24_idx"),
        ),
        migrations.AddIndex(
            model_name="resultatsimulation",
            index=models.Index(fields=["offre_bancaire"], name="credit_res_offre__a8a7b6_idx"),
        ),
        migrations.AddConstraint(
            model_name="profilfinancier",
            constraint=models.CheckConstraint(check=models.Q(("age__gte", 18), ("age__lte", 100)), name="profil_age_ck"),
        ),
        migrations.AddConstraint(
            model_name="projetcredit",
            constraint=models.CheckConstraint(check=models.Q(("montant_souhaite__gt", 0)), name="projet_montant_ck"),
        ),
        migrations.AddConstraint(
            model_name="projetcredit",
            constraint=models.CheckConstraint(check=models.Q(("duree_mois__gt", 0)), name="projet_duree_ck"),
        ),
        migrations.AddConstraint(
            model_name="projetcredit",
            constraint=models.CheckConstraint(check=models.Q(("apport_personnel__gte", 0)), name="projet_apport_ck"),
        ),
    ]

