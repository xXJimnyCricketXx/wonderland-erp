from django.core.management.base import BaseCommand
from django.db.models import Q

from catalog.models import Article


class Command(BaseCommand):
    help = "Assigns sequential WD-XXXX SKUs to every Article (and variant) that doesn't have one yet."

    def handle(self, *args, **options):
        existing_numbers = []
        for sku in Article.objects.exclude(sku__isnull=True).exclude(sku="").values_list("sku", flat=True):
            if sku.startswith("WD-") and sku[3:7].isdigit():
                existing_numbers.append(int(sku[3:7]))
        next_number = max(existing_numbers, default=0) + 1

        missing_sku = Q(sku__isnull=True) | Q(sku="")
        parents = Article.objects.filter(parent_article__isnull=True).filter(missing_sku).order_by("title")

        assigned = 0
        for parent in parents:
            parent.sku = f"WD-{next_number:04d}"
            parent.save(update_fields=["sku"])
            next_number += 1
            assigned += 1

            for variant in parent.variants.filter(missing_sku).order_by("variant_label"):
                variant.sku = f"WD-{next_number:04d}"
                variant.save(update_fields=["sku"])
                next_number += 1
                assigned += 1

        self.stdout.write(self.style.SUCCESS(f"{assigned} Artikel mit fortlaufender SKU versehen."))
