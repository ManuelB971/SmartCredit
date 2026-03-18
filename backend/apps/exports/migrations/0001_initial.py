from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("credit", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExportPdfEmail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email_destinataire", models.EmailField(max_length=254)),
                ("etat", models.CharField(choices=[("EN_ATTENTE", "En attente"), ("ENVOYE", "Envoye"), ("ECHEC", "Echec")], default="EN_ATTENTE", max_length=20)),
                ("date_demande", models.DateTimeField(auto_now_add=True)),
                ("date_envoi", models.DateTimeField(blank=True, null=True)),
                ("erreur", models.TextField(blank=True, null=True)),
                ("simulation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exports_pdf_email", to="credit.simulation")),
            ],
        ),
        migrations.AddIndex(
            model_name="exportpdfemail",
            index=models.Index(fields=["simulation"], name="exports_exp_simula_94fe1b_idx"),
        ),
        migrations.AddIndex(
            model_name="exportpdfemail",
            index=models.Index(fields=["email_destinataire"], name="exports_exp_email__f4f9e3_idx"),
        ),
    ]

