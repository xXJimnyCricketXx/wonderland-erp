from django.core.management.base import BaseCommand

from core.models import ReferenceOption
from core.reference_data import DEFAULT_SEED_DATA


class Command(BaseCommand):
    help = "Seeds default Referenzdaten values (idempotent - safe to re-run, e.g. after a DB reset)."

    def handle(self, *args, **options):
        created = 0
        for category, values in DEFAULT_SEED_DATA.items():
            for order, value in enumerate(values):
                _, was_created = ReferenceOption.objects.get_or_create(
                    category=category, value=value, defaults={"order": order}
                )
                if was_created:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} Referenzwerte angelegt."))
