from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("nom", models.CharField(max_length=100)),
                ("prenom", models.CharField(max_length=100)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_derniere_connexion", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={},
        ),
        migrations.CreateModel(
            name="Consentement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("type", models.CharField(choices=[("CONTACT", "Contact"), ("MARKETING", "Marketing")], max_length=20)),
                ("valeur", models.BooleanField()),
                ("date_consentement", models.DateTimeField(auto_now_add=True)),
                ("source", models.CharField(default="web", max_length=30)),
                (
                    "utilisateur",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="consentements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="consentement",
            constraint=models.CheckConstraint(
                check=models.Q(("utilisateur__isnull", False), ("email__isnull", True))
                | models.Q(("utilisateur__isnull", True), ("email__isnull", False))
                | models.Q(("utilisateur__isnull", False), ("email__isnull", False)),
                name="consentement_identite_ck",
            ),
        ),
        migrations.AddIndex(
            model_name="consentement",
            index=models.Index(fields=["utilisateur"], name="accounts_con_utilisa_4b6a77_idx"),
        ),
        migrations.AddIndex(
            model_name="consentement",
            index=models.Index(fields=["email"], name="accounts_con_email_6760a2_idx"),
        ),
        migrations.AddIndex(
            model_name="consentement",
            index=models.Index(fields=["type"], name="accounts_con_type_390e70_idx"),
        ),
    ]

