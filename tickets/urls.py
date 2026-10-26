
from rest_framework.routers import DefaultRouter

from .views import TicketViewSet, TicketAnalysisViewSet

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")
router.register(
    "ticket-analyses",
    TicketAnalysisViewSet,
    basename="ticket-analysis",
)

urlpatterns = router.urls
