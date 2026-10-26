
from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "customer_name",
        "category",
        "priority",
        "status",
        "created_at",
    )

    list_filter = ("category", "priority", "status")
    search_fields = ("subject", "customer_name", "customer_email")
    ordering = ("-created_at",)
