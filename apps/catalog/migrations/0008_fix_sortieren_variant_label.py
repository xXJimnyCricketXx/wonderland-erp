from django.db import migrations


def fix_sortieren_prefix(apps, schema_editor):
    """Etsy liefert den Variations-Typ als 'Sortieren' statt 'Sorte' (eigener
    Uebersetzungsfehler von Etsy) - korrigiert bereits importierte Varianten,
    kuenftige Importe schreiben dank article_import.py bereits 'Sorte'."""
    Article = apps.get_model("catalog", "Article")
    db_alias = schema_editor.connection.alias
    for article in Article.objects.using(db_alias).filter(variant_label__startswith="Sortieren:"):
        article.variant_label = "Sorte:" + article.variant_label[len("Sortieren:"):]
        article.save(using=db_alias, update_fields=["variant_label"])


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_article_is_sold_out'),
    ]

    operations = [
        migrations.RunPython(fix_sortieren_prefix, migrations.RunPython.noop),
    ]
