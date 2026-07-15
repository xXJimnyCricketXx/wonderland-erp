from django.db import migrations, models


def backfill_missing_invoice_date(apps, schema_editor):
    """Fuer alle bestehenden Einnahmen ohne Rechnungsdatum wird ersatzweise
    das (bisher eigenstaendige) Datum uebernommen, bevor Rechnungsdatum zur
    Pflicht wird - betrifft aktuell keine bekannten Zeilen, ist aber ein
    Sicherheitsnetz fuer Deployments mit anderem Datenstand."""
    Income = apps.get_model("finance", "Income")
    db_alias = schema_editor.connection.alias
    Income.objects.using(db_alias).filter(invoice_date__isnull=True).update(invoice_date=models.F("date"))


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0013_alter_expense_invoice_file_alter_income_invoice_file'),
    ]

    operations = [
        migrations.RunPython(backfill_missing_invoice_date, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='income',
            name='invoice_date',
            field=models.DateField(verbose_name='Rechnungsdatum'),
        ),
    ]
