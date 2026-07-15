from django.core.management.base import BaseCommand
from django.db.models import Q

from catalog.models import Article, next_wd_sku


class Command(BaseCommand):
    help = "Assigns sequential WD-XXXX SKUs to every Article (and variant) that doesn't have one yet."

    def handle(self, *args, **options):
        missing_sku = Q(sku__isnull=True) | Q(sku="")
        parents = Article.objects.filter(parent_article__isnull=True).filter(missing_sku).order_by("title")

        assigned = 0
        for parent in parents:
            parent.sku = next_wd_sku()
            parent.save(update_fields=["sku"])
            assigned += 1

            for variant in parent.variants.filter(missing_sku).order_by("variant_label"):
                variant.sku = next_wd_sku()
                variant.save(update_fields=["sku"])
                assigned += 1

        self.stdout.write(self.style.SUCCESS(f"{assigned} Artikel mit fortlaufender SKU versehen."))
