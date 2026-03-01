"""
Views for notifications app (emails & PDF).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.template.loader import render_to_string

from simulation.models import Simulation


class NotificationViewSet(viewsets.ViewSet):
    """
    Notification API endpoints for emails and PDF generation.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def send_email(self, request):
        """
        Send simulation results by email.
        POST /api/notifications/send_email/
        """
        simulation_id = request.data.get('simulation_id')
        email = request.data.get('email')

        try:
            simulation = Simulation.objects.get(id=simulation_id)

            if not email:
                email = request.user.email

            # Generate email content
            context = {
                'simulation': simulation,
                'results': simulation.resultats.all(),
                'explication': simulation.explication_ia
            }

            html_message = render_to_string('email/simulation_results.html', context)

            send_mail(
                'Résultats de votre simulation Smart Crédit',
                'Veuillez consulter votre email en HTML pour les résultats',
                'noreply@smartcredit.fr',
                [email],
                html_message=html_message,
                fail_silently=False,
            )

            return Response({
                'message': 'Email sent successfully',
                'email': email
            })

        except Simulation.DoesNotExist:
            return Response(
                {'error': 'Simulation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def generate_pdf(self, request):
        """
        Generate PDF report for simulation.
        POST /api/notifications/generate_pdf/
        """
        simulation_id = request.data.get('simulation_id')

        try:
            simulation = Simulation.objects.get(id=simulation_id)

            # TODO: Implement PDF generation with WeasyPrint or ReportLab
            # For now, return placeholder

            return Response({
                'message': 'PDF generation not yet implemented',
                'simulation_id': simulation_id
            })

        except Simulation.DoesNotExist:
            return Response(
                {'error': 'Simulation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
