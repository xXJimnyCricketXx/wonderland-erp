from django.db import migrations

# Official LUCID material codes, matching the fixed order the 8 categories
# were seeded in (knowledge/0007_seed_material_categories.py).
LUCID_CODES = {
    "Glas": "10000",
    "Pappe, Papier, Karton": "20000",
    "Eisenmetalle": "30000",
    "Aluminium": "40000",
    "Kunststoffe": "50000",
    "Getränkekartonverpackungen": "60000",
    "Sonstige Verbundverpackungen": "70000",
    "Sonstige Materialien": "80000",
}


def seed_codes(apps, schema_editor):
    MaterialCategory = apps.get_model("knowledge", "MaterialCategory")
    for name, code in LUCID_CODES.items():
        MaterialCategory.objects.filter(name=name).update(lucid_material_code=code)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0012_packaginglicensedatareport_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_codes, noop),
    ]
