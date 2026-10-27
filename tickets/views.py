
import logging

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render

from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket, TicketAnalysis
from .serializers import TicketSerializer, TicketAnalysisSerializer
from .ai_service import analyze_ticket, generate_customer_reply


logger = logging.getLogger(__name__)


# =========================================================
# PUBLIC HOMEPAGE
# =========================================================

def home(request):
    """Render the public project homepage."""
    return render(request, "tickets/home.html")


# =========================================================
# USER REGISTRATION
# =========================================================

class RegisterView(APIView):
    """Register a regular dashboard user."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "")
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(email, str):
            return Response(
                {"error": "Invalid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = username.strip()
        email = email.strip()

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(username) > 150:
            return Response(
                {"error": "Username must be 150 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()

        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"error": "That username is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data = {
            "username": username,
            "password": password,
        }

        if email:
            user_data["email"] = email

        try:
            validate_password(password)
        except ValidationError as error:
            return Response(
                {"error": list(error.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.create_user(**user_data)
            token = Token.objects.create(user=user)

        except Exception:
            logger.exception("Dashboard registration failed")
            return Response(
                {
                    "error": (
                        "Could not create your account. "
                        "Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Account created successfully.",
                "username": user.get_username(),
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# USER LOGIN
# =========================================================

class LoginView(APIView):
    """Authenticate an existing Django user."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")

        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or not username.strip()
            or not password
        ):
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = username.strip()

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None or not user.is_active:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Keep the shared dashboard service account separate.
        if user.get_username() == "support_dashboard_api":
            return Response(
                {
                    "error": (
                        "This account cannot log in to the dashboard."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "username": user.get_username(),
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# USER LOGOUT
# =========================================================

class LogoutView(APIView):
    """Revoke the authenticated user's token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.get_username() == "support_dashboard_api":
            return Response(
                {
                    "error": (
                        "The dashboard service account "
                        "cannot log out here."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        request.user.auth_token.delete()

        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


# =========================================================
# TICKET MANAGEMENT AND AI OPERATIONS
# =========================================================


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only tickets owned by the authenticated user."""
        return Ticket.objects.filter(
            created_by=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        """Assign every new ticket to its authenticated owner."""
        serializer.save(created_by=self.request.user)

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



# =========================================================
# TICKET ANALYSIS HISTORY
# =========================================================

class TicketAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TicketAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return analysis history for the current user's tickets only."""
        return TicketAnalysis.objects.filter(
            ticket__created_by=self.request.user
        ).order_by("-created_at")
