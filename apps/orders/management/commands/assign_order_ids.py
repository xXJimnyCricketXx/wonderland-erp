from django.core.management.base import BaseCommand

from data_import.order_import import assign_order_ids


class Command(BaseCommand):
    help = (
        "Assigns sequential internal Bestell-IDs (B-0001, B-0002, ...) to "
        "orders that don't have one yet, oldest sale_date first."
    )

    def handle(self, *args, **options):
        assigned = assign_order_ids()
        self.stdout.write(self.style.SUCCESS(f"{assigned} Bestellungen mit fortlaufender Bestell-ID versehen."))
