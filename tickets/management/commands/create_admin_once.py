import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a production superuser using environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")

        if not username or not password:
            raise CommandError("Admin environment variables are missing.")

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            raise CommandError("This username already exists.")

        User.objects.create_superuser(
            username=username,
            email="",
            password=password,
        )

        self.stdout.write(self.style.SUCCESS("Admin account created."))