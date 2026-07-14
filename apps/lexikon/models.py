from django.db import models


class Gemstone(models.Model):
    """Heilstein-Lexikon. Lives in its own database (lexikon.sqlite3, see
    DATABASE_ROUTERS in settings) so it stays a portable, self-contained
    reference dataset that other projects could reuse - deliberately no FKs
    to models in the default DB. The app queries across DBs by matching on
    name/text (e.g. article title against Gemstone.name), never via FK."""

    name = models.CharField("Name", max_length=255)

    # Als Blob in dieser DB statt als Datei im gemeinsamen MEDIA_ROOT - das
    # Bild reist damit automatisch mit lexikon.sqlite3 mit, wenn diese DB
    # irgendwann eigenstaendig in ein anderes Projekt uebernommen wird, statt
    # zusaetzlich einen media/gemstones/-Ordner separat mitkopieren zu muessen.
    image_data = models.BinaryField("Bilddaten", blank=True, null=True, editable=False)
    image_content_type = models.CharField("Bild-Content-Type", max_length=100, blank=True, editable=False)
    image_filename = models.CharField("Bild-Dateiname", max_length=255, blank=True, editable=False)

    # Allgemeine Informationen
    description = models.TextField("Beschreibung", blank=True)
    alternative_names = models.CharField("Alternative Namen", max_length=500, blank=True)
    origin = models.CharField("Herkunft", max_length=255, blank=True)
    confusable_with = models.CharField("Verwechslungen", max_length=500, blank=True)
    counterfeits = models.CharField("Fälschungen", max_length=500, blank=True)

    # Mineralogie
    mineral_class = models.CharField("Mineralklasse", max_length=255, blank=True)
    chemical_composition = models.CharField("Chemische Zusammensetzung", max_length=255, blank=True)
    formation = models.TextField("Entstehung", blank=True)
    crystal_system = models.CharField("Kristallsystem", max_length=100, blank=True)

    # Eigenschaften
    mohs_hardness = models.CharField("Mohshärte", max_length=50, blank=True)
    density = models.CharField("Dichte", max_length=100, blank=True)
    cleavage = models.CharField("Spaltbarkeit", max_length=255, blank=True)
    fracture = models.CharField("Bruchverhalten", max_length=255, blank=True)

    # Farbliche Eigenschaften
    transparency = models.CharField("Transparenz", max_length=100, blank=True)
    color = models.CharField("Farbe", max_length=255, blank=True)
    luster = models.CharField("Glanz", max_length=100, blank=True)
    streak = models.CharField("Strichfarbe", max_length=100, blank=True)

    # Wirkungen
    organ_effect = models.TextField("Organwirkung", blank=True)
    physical_effect = models.TextField("Körperliche Wirkung", blank=True)
    emotional_effect = models.TextField("Seelische Wirkung", blank=True)
    # Free text on purpose - symptom/application language is too colloquial
    # for a fixed tag list to search well (e.g. "Kopfschmerzen", "innere Unruhe").
    application = models.TextField("Anwendung", blank=True)

    # Sonstiges
    bach_flower = models.CharField("Ergänzende Bachblüte", max_length=255, blank=True)
    astrological_sign = models.CharField("Astrologische Zuordnung", max_length=255, blank=True)
    chakra = models.CharField("Chakra-Zuordnung", max_length=255, blank=True)
    feng_shui = models.CharField("Feng-Shui-Zuordnung", max_length=255, blank=True)
    care_instructions = models.TextField("Pflege", blank=True)
    notes = models.TextField("Hinweise/Bemerkungen", blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Heilstein"
        verbose_name_plural = "Heilsteine"
        ordering = ["name"]

    def __str__(self):
        return self.name
