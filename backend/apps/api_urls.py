from django.urls import path

from apps.accounts import api as auth_api
from apps.accounts.jwt_api import SmartCreditTokenObtainPairView, SmartCreditTokenRefreshView
from apps.credit import api as credit_api
from apps.exports import api as export_api

urlpatterns = [
    path("auth/register/", auth_api.register, name="register"),
    path("auth/me/", auth_api.me, name="me"),
    path("auth/token/", SmartCreditTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", SmartCreditTokenRefreshView.as_view(), name="token_refresh"),
    path("simulations/", credit_api.create_simulation, name="create_simulation"),
    path("simulations/<int:simulation_id>/", credit_api.get_simulation, name="get_simulation"),
    path("simulations/<int:simulation_id>/calcul/", credit_api.calculate_simulation, name="calculate_simulation"),
    path("users/me/simulations/", credit_api.my_simulations, name="my_simulations"),
    path("simulations/<int:simulation_id>/export-email/", export_api.export_email, name="export_email"),
    path("offres/", credit_api.list_offres, name="list_offres"),
]

