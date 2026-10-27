from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    TicketViewSet,
    TicketAnalysisViewSet,
)

router = DefaultRouter()

router.register(
    "tickets",
    TicketViewSet,
    basename="ticket",
)

router.register(
    "ticket-analyses",
    TicketAnalysisViewSet,
    basename="ticket-analysis",
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-logout"),
] + router.urls