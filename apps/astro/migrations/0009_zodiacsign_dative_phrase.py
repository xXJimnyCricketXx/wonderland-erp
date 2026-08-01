from django.db import migrations, models

DATIVE_PHRASES = {
    "widder": "im Widder",
    "stier": "im Stier",
    "zwillinge": "in den Zwillingen",
    "krebs": "im Krebs",
    "loewe": "im Löwen",
    "jungfrau": "in der Jungfrau",
    "waage": "in der Waage",
    "skorpion": "im Skorpion",
    "schuetze": "im Schützen",
    "steinbock": "im Steinbock",
    "wassermann": "im Wassermann",
    "fische": "in den Fischen",
}


def seed(apps, schema_editor):
    ZodiacSign = apps.get_model("astro", "ZodiacSign")
    db_alias = schema_editor.connection.alias
    for key, phrase in DATIVE_PHRASES.items():
        ZodiacSign.objects.using(db_alias).filter(key=key).update(dative_phrase=phrase)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('astro', '0008_remove_reportbranding_cover_background_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='zodiacsign',
            name='dative_phrase',
            field=models.CharField(blank=True, max_length=50, verbose_name='Dativ-Wendung (z. B. „im Löwen“)'),
        ),
        migrations.RunPython(seed, noop),
    ]
