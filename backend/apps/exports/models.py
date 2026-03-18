from django.db import models


class EtatExport(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE"
    ENVOYE = "ENVOYE"
    ECHEC = "ECHEC"


class ExportPdfEmail(models.Model):
    simulation = models.ForeignKey("credit.Simulation", on_delete=models.CASCADE, related_name="exports_pdf_email")
    email_destinataire = models.EmailField()
    etat = models.CharField(max_length=20, choices=EtatExport.choices, default=EtatExport.EN_ATTENTE)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    erreur = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["simulation"]),
            models.Index(fields=["email_destinataire"]),
        ]

