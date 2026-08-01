from django.db import migrations


def seed(apps, schema_editor):
    Planet = apps.get_model("astro", "Planet")
    Planet.objects.using(schema_editor.connection.alias).update_or_create(
        key="mondknoten",
        defaults=dict(name_de="Mondknoten", is_angle=False, is_optional_body=True),
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('astro', '0003_seed_reference_data'),
    ]

    operations = [
        migrations.RunPython(seed, noop),
    ]
