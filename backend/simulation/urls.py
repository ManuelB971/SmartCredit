"""
URL configuration for simulation app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SimulationViewSet, OffreBancaireViewSet

router = DefaultRouter()
router.register(r'simulations', SimulationViewSet, basename='simulation')
router.register(r'offres-bancaires', OffreBancaireViewSet, basename='offre-bancaire')

urlpatterns = [
    path('', include(router.urls)),
]
