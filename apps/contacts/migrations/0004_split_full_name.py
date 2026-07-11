from django.db import migrations, models


def split_full_name(apps, schema_editor):
    for model_name in ("Customer", "Supplier"):
        model = apps.get_model("contacts", model_name)
        for obj in model.objects.all():
            name = (obj.full_name or "").strip()
            if " " in name:
                first, last = name.rsplit(" ", 1)
            else:
                first, last = name, ""
            obj.first_name = first
            obj.last_name = last
            obj.save(update_fields=["first_name", "last_name"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0003_alter_customer_options_alter_supplier_options_and_more"),
    ]

    operations = [
        migrations.RunPython(split_full_name, noop_reverse),
        migrations.RemoveField(model_name="customer", name="full_name"),
        migrations.RemoveField(model_name="supplier", name="full_name"),
        migrations.AlterField(
            model_name="customer",
            name="first_name",
            field=models.CharField(max_length=255, verbose_name="Vorname"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="last_name",
            field=models.CharField(max_length=255, verbose_name="Nachname"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="first_name",
            field=models.CharField(max_length=255, verbose_name="Vorname"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="last_name",
            field=models.CharField(max_length=255, verbose_name="Nachname"),
        ),
        migrations.AlterModelOptions(
            name="customer",
            options={"ordering": ["last_name", "first_name"], "verbose_name": "Kunde", "verbose_name_plural": "Kunden"},
        ),
        migrations.AlterModelOptions(
            name="supplier",
            options={"ordering": ["last_name", "first_name"], "verbose_name": "Lieferant", "verbose_name_plural": "Lieferanten"},
        ),
    ]
