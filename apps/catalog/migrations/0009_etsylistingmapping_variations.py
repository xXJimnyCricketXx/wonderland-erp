from django.db import migrations, models


def split_mappings_by_variation(apps, schema_editor):
    """Bisher eine Zeile je Listing-ID, egal wie viele echte Sorten/Groessen
    darunter liefen - splittet in eine Zeile je tatsaechlich vorkommender
    Variante. Listings mit nur einer (oder keiner) Variante behalten ihre
    bestehende Artikel-Zuordnung 1:1, nur die neue variations-Spalte wird
    befuellt. Listings mit mehreren Varianten hatten zum Zeitpunkt dieser
    Migration ausnahmslos noch keinen Artikel zugeordnet (article_id war
    immer NULL), es geht also keine bestehende Zuordnung verloren."""
    EtsyListingMapping = apps.get_model("catalog", "EtsyListingMapping")
    OrderItem = apps.get_model("orders", "OrderItem")
    db_alias = schema_editor.connection.alias

    for mapping in list(EtsyListingMapping.objects.using(db_alias).all()):
        variations_present = list(
            OrderItem.objects.using(db_alias)
            .filter(listing_id=mapping.listing_id)
            .values_list("variations", flat=True)
            .distinct()
        )
        if not variations_present:
            continue

        mapping.variations = variations_present[0]
        mapping.save(using=db_alias, update_fields=["variations"])

        for extra_variation in variations_present[1:]:
            EtsyListingMapping.objects.using(db_alias).get_or_create(
                listing_id=mapping.listing_id,
                variations=extra_variation,
                defaults={"item_name": mapping.item_name, "article_id": None},
            )


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_fix_sortieren_variant_label'),
        ('orders', '0010_alter_order_etsy_receipt_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='etsylistingmapping',
            name='variations',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Variante'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='etsylistingmapping',
            name='listing_id',
            field=models.CharField(max_length=50, verbose_name='Etsy-Listing-ID'),
        ),
        migrations.AlterModelOptions(
            name='etsylistingmapping',
            options={'ordering': ['item_name', 'variations'], 'verbose_name': 'Etsy-Listing-Zuordnung', 'verbose_name_plural': 'Etsy-Listing-Zuordnungen'},
        ),
        migrations.RunPython(split_mappings_by_variation, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='etsylistingmapping',
            unique_together={('listing_id', 'variations')},
        ),
    ]
