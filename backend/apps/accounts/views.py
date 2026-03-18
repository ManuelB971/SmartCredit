import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import User


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_http_methods(["POST"])
def register(request: HttpRequest):
    data = _json_body(request)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    nom = (data.get("nom") or "").strip()
    prenom = (data.get("prenom") or "").strip()

    if not (email and password and nom and prenom):
        return JsonResponse({"error": "Champs requis: email, password, nom, prenom"}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email déjà utilisé"}, status=409)

    user = User.objects.create_user(email=email, password=password, nom=nom, prenom=prenom)
    login(request, user)
    return JsonResponse({"id": user.id, "email": user.email, "nom": user.nom, "prenom": user.prenom})


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request: HttpRequest):
    data = _json_body(request)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not (email and password):
        return JsonResponse({"error": "Champs requis: email, password"}, status=400)

    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({"error": "Identifiants invalides"}, status=401)

    login(request, user)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request: HttpRequest):
    logout(request)
    return JsonResponse({"ok": True})

