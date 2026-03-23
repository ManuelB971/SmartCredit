from io import BytesIO

from celery import shared_task
from django.core.mail import EmailMessage
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import ExportPdfEmail, EtatExport


def _build_simulation_pdf(export: ExportPdfEmail) -> bytes:
    sim = export.simulation
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(48, y, "SmartCredit - Recapitulatif de simulation")

    c.setFont("Helvetica", 11)
    y -= 36
    c.drawString(48, y, f"Simulation ID: {sim.id}")
    y -= 18
    c.drawString(48, y, f"Type de credit: {sim.type_credit}")
    y -= 18
    c.drawString(48, y, f"Date de simulation: {sim.date_simulation.strftime('%Y-%m-%d %H:%M')}")

    profil = getattr(sim, "profil_financier", None)
    if profil:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(48, y, "Profil financier")
        c.setFont("Helvetica", 11)
        y -= 18
        c.drawString(48, y, f"Revenus mensuels: {profil.revenus_mensuels}")
        y -= 18
        c.drawString(48, y, f"Charges logement: {profil.charges_logement}")
        y -= 18
        c.drawString(48, y, f"Charges credits: {profil.charges_credits}")

    projet = getattr(sim, "projet_credit", None)
    if projet:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(48, y, "Projet credit")
        c.setFont("Helvetica", 11)
        y -= 18
        c.drawString(48, y, f"Montant souhaite: {projet.montant_souhaite}")
        y -= 18
        c.drawString(48, y, f"Duree (mois): {projet.duree_mois}")
        y -= 18
        c.drawString(48, y, f"Apport personnel: {projet.apport_personnel}")

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_export_pdf_email(self, export_id: int):
    export = (
        ExportPdfEmail.objects.select_related("simulation", "simulation__profil_financier", "simulation__projet_credit")
        .get(id=export_id)
    )

    try:
        pdf_bytes = _build_simulation_pdf(export)
        subject = f"Votre recapitulatif SmartCredit - simulation #{export.simulation_id}"
        body = (
            "Bonjour,\n\n"
            "Veuillez trouver en piece jointe le recapitulatif PDF de votre simulation SmartCredit.\n\n"
            "Ceci est un envoi automatique."
        )
        mail = EmailMessage(subject=subject, body=body, to=[export.email_destinataire])
        mail.attach(f"simulation_{export.simulation_id}.pdf", pdf_bytes, "application/pdf")
        mail.send(fail_silently=False)

        export.etat = EtatExport.ENVOYE
        export.date_envoi = timezone.now()
        export.erreur = None
        export.save(update_fields=["etat", "date_envoi", "erreur"])
    except Exception as exc:
        export.etat = EtatExport.ECHEC
        export.erreur = str(exc)[:2000]
        export.save(update_fields=["etat", "erreur"])
        raise
