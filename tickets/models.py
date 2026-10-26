from django.db import models

# Create your models here.

from django.db import models


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ("technical", "Technical Issue"),
        ("billing", "Billing"),
        ("account", "Account"),
        ("general", "General"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    subject = models.CharField(max_length=255)
    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="general",
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.customer_name}"


class TicketAnalysis(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    summary = models.TextField()
    category = models.CharField(max_length=20)
    priority = models.CharField(max_length=10)
    customer_issue = models.TextField()
    recommended_action = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for ticket {self.ticket_id}"
