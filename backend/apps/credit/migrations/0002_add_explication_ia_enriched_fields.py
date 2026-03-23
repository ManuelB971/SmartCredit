# Generated manually for ExplicationIA enriched fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("credit", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="explicationia",
            name="resume_executif",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="explicationia",
            name="donnees_enrichies",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
