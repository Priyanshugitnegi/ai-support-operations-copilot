
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Ensure the dashboard API token exists in the database"

    def handle(self, *args, **options):
        token_key = os.getenv("DJANGO_API_TOKEN", "").strip()

        if not token_key:
            raise CommandError(
                "DJANGO_API_TOKEN is not configured."
            )

        User = get_user_model()
        username = "support_dashboard_api"

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        Token.objects.filter(user=user).exclude(
            key=token_key
        ).delete()

        token, created = Token.objects.get_or_create(
            key=token_key,
            defaults={"user": user},
        )

        if token.user_id != user.pk:
            raise CommandError(
                "The configured API token belongs to another user. "
                "No token ownership was changed."
            )

        action = "created" if created else "already exists"
        self.stdout.write(
            self.style.SUCCESS(
                f"Dashboard API token {action}."
            )
        )
