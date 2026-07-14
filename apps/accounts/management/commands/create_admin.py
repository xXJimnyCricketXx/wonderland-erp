from decouple import config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """Legt beim ersten Container-Start automatisch einen Admin-Account an,
    falls noch kein Superuser existiert - Zugangsdaten kommen aus
    ADMIN_USERNAME/ADMIN_PASSWORD (Docker/Unraid-Template), nicht aus
    Kommandozeilen-Argumenten. Ohne ADMIN_PASSWORD passiert nichts, der
    Account kann dann später wie gewohnt per createsuperuser angelegt werden."""

    help = "Legt einen initialen Admin-Account aus ADMIN_USERNAME/ADMIN_PASSWORD an, falls noch keiner existiert."

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Admin-Account bereits vorhanden, überspringe.")
            return

        password = config("ADMIN_PASSWORD", default="")
        if not password:
            self.stdout.write("ADMIN_PASSWORD nicht gesetzt, überspringe Admin-Erstellung.")
            return

        username = config("ADMIN_USERNAME", default="admin")
        User.objects.create_superuser(username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f"Admin-Account '{username}' angelegt."))
