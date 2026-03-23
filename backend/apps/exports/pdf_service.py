"""
Génération du rapport PDF de simulation et envoi par email.
"""
import io
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from apps.credit.models import Simulation
from .models import ExportPdfEmail, EtatExport


def _fmt(value, decimals=2):
    """Format number for display."""
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        return f"{float(value):,.2f}".replace(",", " ").replace(".", ",")
    return str(value)


def generate_simulation_pdf(simulation: Simulation) -> bytes:
    """Génère le PDF du rapport de simulation."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#006554"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#006554"),
        spaceAfter=8,
    )

    story = []
    story.append(Paragraph("Rapport de simulation Smart Crédit", title_style))
    story.append(Paragraph(f"Simulation #{simulation.id} — {simulation.get_type_credit_display()}", styles["Normal"]))
    story.append(Paragraph(f"Date : {simulation.date_simulation.strftime('%d/%m/%Y à %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Profil financier
    sit_fam_labels = {"CELIBATAIRE": "Célibataire", "MARIE": "Marié(e)", "PACS": "Pacsé(e)"}
    pf = simulation.profil_financier
    story.append(Paragraph("Profil financier", heading_style))
    pf_data = [
        ["Âge", str(pf.age)],
        ["Situation familiale", sit_fam_labels.get(pf.situation_familiale, pf.situation_familiale or "—")],
        ["Nombre d'enfants", str(pf.nombre_enfants)],
        ["Revenus mensuels", f"{_fmt(pf.revenus_mensuels)} €"],
        ["Autres revenus", f"{_fmt(pf.autres_revenus)} €"],
        ["Charges logement", f"{_fmt(pf.charges_logement)} €"],
        ["Charges crédits", f"{_fmt(pf.charges_credits)} €"],
        ["Autres charges", f"{_fmt(pf.autres_charges)} €"],
        ["Type de contrat", pf.type_contrat or "—"],
        ["Ancienneté emploi", f"{pf.anciennete_emploi_mois or 0} mois"],
    ]
    t_pf = Table(pf_data, colWidths=[5 * cm, 8 * cm])
    t_pf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f3f2")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1c1b1b")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc9c4")),
    ]))
    story.append(t_pf)
    story.append(Spacer(1, 20))

    # Projet crédit
    pc = simulation.projet_credit
    story.append(Paragraph("Projet de crédit", heading_style))
    pc_data = [
        ["Montant souhaité", f"{_fmt(pc.montant_souhaite)} €"],
        ["Apport personnel", f"{_fmt(pc.apport_personnel)} €"],
        ["Durée", f"{pc.duree_mois} mois ({pc.duree_mois // 12} ans)"],
    ]
    t_pc = Table(pc_data, colWidths=[5 * cm, 8 * cm])
    t_pc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f3f2")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc9c4")),
    ]))
    story.append(t_pc)
    story.append(Spacer(1, 20))

    # Résultats par scénario — disposition compacte pour éviter le débordement
    resultats = list(simulation.resultats.select_related("offre_bancaire__banque").all())
    if resultats:
        story.append(Paragraph("Résultats par scénario", heading_style))
        scenario_labels = {"PRUDENT": "Prudent", "EQUILIBRE": "Équilibré", "CONFORT": "Confort"}
        res_data = [["Scénario", "Banque", "Mensualité", "Intérêts", "TE %", "R.A.V."]]
        for r in sorted(resultats, key=lambda x: ["PRUDENT", "EQUILIBRE", "CONFORT"].index(x.scenario) if x.scenario else 9):
            banque = (r.offre_bancaire.banque.nom[:18] + "…") if (r.offre_bancaire and len(r.offre_bancaire.banque.nom) > 18) else (r.offre_bancaire.banque.nom if r.offre_bancaire else "—")
            res_data.append([
                scenario_labels.get(r.scenario, r.scenario or "—"),
                banque,
                f"{_fmt(r.mensualite)} €",
                f"{_fmt(r.cout_total)} €",
                f"{_fmt(r.taux_endettement, 1)}",
                f"{_fmt(r.reste_a_vivre)} €",
            ])
        # Largeurs adaptées à A4 (17 cm utiles) : 2.5 + 3.5 + 2.5 + 2.5 + 1.5 + 2.5 = 15 cm
        t_res = Table(res_data, colWidths=[2.5 * cm, 3.5 * cm, 2.5 * cm, 2.5 * cm, 1.5 * cm, 2.5 * cm])
        t_res.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#006554")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc9c4")),
        ]))
        story.append(t_res)
        story.append(Spacer(1, 20))

    # Explication IA
    expl = getattr(simulation, "explication_ia", None)
    if expl and expl.texte_explication:
        story.append(Paragraph("Avis Smart AI", heading_style))
        if getattr(expl, "resume_executif", None) and expl.resume_executif:
            story.append(Paragraph(f"<b>{expl.resume_executif}</b>", styles["Normal"]))
            story.append(Spacer(1, 6))
        story.append(Paragraph(expl.texte_explication.replace("\n", "<br/>"), styles["Normal"]))
        donnees = getattr(expl, "donnees_enrichies", None) or {}
        pts_forts = donnees.get("points_forts_dossier", [])
        risques = donnees.get("risques_identifies", [])
        if pts_forts or risques:
            story.append(Spacer(1, 8))
            if pts_forts:
                story.append(Paragraph("<b>Points forts :</b> " + " ; ".join(pts_forts), styles["Normal"]))
            if risques:
                story.append(Paragraph("<b>Points d'attention :</b> " + " ; ".join(risques), styles["Normal"]))
        if expl.recommandations:
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"<b>Recommandations :</b> {expl.recommandations.replace(chr(10), '<br/>')}", styles["Normal"]))
        prochaines = donnees.get("prochaines_etapes", [])
        if prochaines:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Prochaines étapes :</b>", styles["Normal"]))
            for etape in prochaines:
                story.append(Paragraph(f"• {etape}", styles["Normal"]))

    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Ce document est indicatif et ne constitue pas une offre contractuelle. Consultez un conseiller pour valider votre situation.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)
    return buffer.getvalue()


def is_email_configured() -> bool:
    """Vérifie si l'envoi d'email est configuré."""
    return bool(
        getattr(settings, "EMAIL_HOST", None)
        and getattr(settings, "EMAIL_HOST_USER", None)
        and getattr(settings, "EMAIL_HOST_PASSWORD", None)
    )


def send_simulation_pdf_email(export: ExportPdfEmail) -> bool:
    """
    Génère le PDF et envoie l'email. Met à jour l'état de l'export.
    Retourne True en cas de succès, False sinon.
    """
    if not is_email_configured():
        export.etat = EtatExport.ECHEC
        export.erreur = "Configuration email manquante (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)"
        export.save(update_fields=["etat", "erreur"])
        return False

    sim = export.simulation
    try:
        pdf_bytes = generate_simulation_pdf(sim)
    except Exception as e:
        export.etat = EtatExport.ECHEC
        export.erreur = f"Erreur génération PDF: {str(e)[:500]}"
        export.save(update_fields=["etat", "erreur"])
        return False

    type_label = "Immobilier" if sim.type_credit == "IMMOBILIER" else "Étudiant"
    subject = f"Smart Crédit — Rapport de simulation #{sim.id} ({type_label})"
    body = f"""Bonjour,

Vous avez demandé à recevoir le rapport de votre simulation de crédit par email.

Ci-joint le document PDF récapitulatif de votre simulation #{sim.id}.

Cordialement,
L'équipe Smart Crédit
"""

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[export.email_destinataire],
    )
    email.attach(
        f"simulation_smartcredit_{sim.id}.pdf",
        pdf_bytes,
        "application/pdf",
    )

    try:
        email.send(fail_silently=False)
        export.etat = EtatExport.ENVOYE
        export.date_envoi = timezone.now()
        export.erreur = None
        export.save(update_fields=["etat", "date_envoi", "erreur"])
        return True
    except Exception as e:
        export.etat = EtatExport.ECHEC
        export.erreur = f"Erreur envoi email: {str(e)[:500]}"
        export.save(update_fields=["etat", "erreur"])
        return False
