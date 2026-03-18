from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_connexion = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = ["nom", "prenom"]

    def __str__(self) -> str:
        return self.email

    @property
    def is_anonymous(self) -> bool:  # Django-compatible
        return False

    @property
    def is_authenticated(self) -> bool:  # Django-compatible
        return True


class Consentement(models.Model):
    class Type(models.TextChoices):
        CONTACT = "CONTACT"
        MARKETING = "MARKETING"

    utilisateur = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="consentements"
    )
    email = models.EmailField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    valeur = models.BooleanField()
    date_consentement = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=30, default="web")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(utilisateur__isnull=False) | models.Q(email__isnull=False),
                name="consentement_identite_ck",
            )
        ]
        indexes = [
            models.Index(fields=["utilisateur"]),
            models.Index(fields=["email"]),
            models.Index(fields=["type"]),
        ]

