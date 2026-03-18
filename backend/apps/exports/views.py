import json

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.credit.models import Simulation
from .models import ExportPdfEmail


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_http_methods(["POST"])
def export_email(request: HttpRequest, simulation_id: int):
    data = _json_body(request)
    email = (data.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"error": "email requis"}, status=400)
    try:
        sim = Simulation.objects.get(id=simulation_id)
    except Simulation.DoesNotExist:
        return JsonResponse({"error": "Simulation introuvable"}, status=404)

    export = ExportPdfEmail.objects.create(simulation=sim, email_destinataire=email)
    return JsonResponse({"ok": True, "export_id": export.id, "etat": export.etat})

