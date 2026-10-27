
import logging

from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Ticket, TicketAnalysis
from .serializers import TicketSerializer, TicketAnalysisSerializer
from .ai_service import analyze_ticket, generate_customer_reply


logger = logging.getLogger(__name__)


def home(request):
    """Render the public project homepage."""
    return render(request, "tickets/home.html")


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        ticket = self.get_object()

        try:
            analysis = analyze_ticket(
                subject=ticket.subject,
                description=ticket.description,
            )

            saved_analysis = TicketAnalysis.objects.create(
                ticket=ticket,
                summary=analysis.summary,
                category=analysis.category,
                priority=analysis.priority,
                customer_issue=analysis.customer_issue,
                recommended_action=analysis.recommended_action,
            )

            return Response(
                {
                    "id": saved_analysis.id,
                    "ticket_id": ticket.id,
                    "summary": saved_analysis.summary,
                    "category": saved_analysis.category,
                    "priority": saved_analysis.priority,
                    "customer_issue": saved_analysis.customer_issue,
                    "recommended_action": saved_analysis.recommended_action,
                    "created_at": saved_analysis.created_at,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Ticket analysis failed")

            return Response(
                {
                    "error": "Ticket analysis failed. Please try again."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="generate-reply",
    )
    def generate_reply(self, request, pk=None):
        ticket = self.get_object()

        try:
            reply = generate_customer_reply(
                subject=ticket.subject,
                description=ticket.description,
            )

            return Response(
                {
                    "ticket_id": ticket.id,
                    "customer_reply": reply.customer_reply,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception(
                "Customer reply generation failed for ticket %s",
                ticket.id,
            )

            return Response(
                {
                    "error": (
                        "Customer reply generation failed. "
                        "Please try again."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class TicketAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TicketAnalysis.objects.all().order_by("-created_at")
    serializer_class = TicketAnalysisSerializer
    permission_classes = [IsAuthenticated]
