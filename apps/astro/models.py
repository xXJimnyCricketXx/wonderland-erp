from django.core.exceptions import ValidationError
from django.db import models


class TrackedText(models.Model):
    """Abstrakte Basis fuer redaktionell gepflegte Texte: einheitlicher
    Status-Workflow (Entwurf/Geprueft/Veroeffentlicht) + Autor-Tracking."""

    STATUS = [
        ("draft", "Entwurf"),
        ("reviewed", "Geprüft"),
        ("published", "Veröffentlicht"),
    ]

    status = models.CharField("Status", max_length=20, choices=STATUS, default="draft")
    author = models.CharField("Verfasst von", max_length=100, blank=True)
    reviewed_by = models.CharField("Geprüft von", max_length=100, blank=True)
    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        abstract = True


class StoredImage(models.Model):
    """Abstrakte Basis fuer Bilder, die direkt als Binaerdaten in astro.db
    liegen statt im media-Ordner - diese Bilder werden nur beim
    serverseitigen PDF-Bau eingebettet (nie live an den Browser
    ausgeliefert), so bleibt astro.db komplett eigenstaendig/portabel,
    genau wie Gemstone.image_data im Heilstein-Lexikon."""

    image_data = models.BinaryField("Bilddaten", blank=True, null=True, editable=False)
    content_type = models.CharField("Content-Type", max_length=50, default="image/png", editable=False)

    class Meta:
        abstract = True


class ZodiacSign(models.Model):
    """Stammdaten - redaktionell/per Fixture gepflegt, nicht ueber die UI."""

    ELEMENTS = [
        ("feuer", "Feuer"),
        ("erde", "Erde"),
        ("luft", "Luft"),
        ("wasser", "Wasser"),
    ]
    QUALITIES = [
        ("kardinal", "Kardinal"),
        ("fix", "Fix"),
        ("veraenderlich", "Veränderlich"),
    ]

    key = models.SlugField("Schlüssel", unique=True)
    name_de = models.CharField("Name", max_length=50)
    element = models.CharField("Element", max_length=20, choices=ELEMENTS)
    quality = models.CharField("Qualität", max_length=20, choices=QUALITIES)
    # Bei Zeichen mit zwei traditionellen Herrschern (Skorpion, Wassermann,
    # Fische) steht hier bewusst der MODERNE Herrscher (Pluto, Uranus,
    # Neptun) - astroschmids eigene Vorlagen nutzen ebenfalls den modernen
    # Herrscher, nicht den klassischen. Wird fuer die automatisch generierte
    # Hausherr-Titelzeile gebraucht (siehe HausherrAszendentText.ruler_planet).
    ruler_planet = models.ForeignKey(
        "Planet", verbose_name="Herrscherplanet", on_delete=models.PROTECT,
        related_name="+", null=True, blank=True,
    )
    # Kleines Symbol/Glyph (z.B. fuer eingebettete Nutzung in der
    # Kurzbeschreibung) - je PNG und SVG, damit je nach Einsatzort das
    # passende Format zur Verfuegung steht (SVG fuer verlustfreie Skalierung
    # im PDF, PNG als Fallback/fuer Kontexte ohne SVG-Unterstuetzung).
    symbol_image_png = models.BinaryField("Symbolbild (PNG)", blank=True, null=True, editable=False)
    symbol_image_svg = models.BinaryField("Symbolbild (SVG)", blank=True, null=True, editable=False)
    # Groessere Zeichen-Illustration fuer dynamisch gebaute Deckblaetter
    # (auf ReportBranding.cover_background platziert) - ebenfalls PNG+SVG.
    zodiac_image_png = models.BinaryField("Zeichenbild (PNG)", blank=True, null=True, editable=False)
    zodiac_image_svg = models.BinaryField("Zeichenbild (SVG)", blank=True, null=True, editable=False)
    # Fuer die feste Kapitelueberschrift "Mond {dative_phrase}" (z.B. "im
    # Loewen", "in der Jungfrau", "in den Fischen") - je nach Genus/Numerus
    # des Zeichennamens ein anderer Artikel/Fall, laesst sich nicht aus
    # name_de herleiten (deutsche Grammatik-Sonderfaelle), deshalb redaktionell
    # gepflegt statt automatisch generiert.
    dative_phrase = models.CharField("Dativ-Wendung (z. B. „im Löwen“)", max_length=50, blank=True)
    sort_order = models.PositiveSmallIntegerField("Sortierung", default=0)

    class Meta:
        verbose_name = "Tierkreiszeichen"
        verbose_name_plural = "Tierkreiszeichen"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name_de


class Planet(models.Model):
    key = models.SlugField("Schlüssel", unique=True)
    name_de = models.CharField("Name", max_length=50)
    is_angle = models.BooleanField("Achsenpunkt (Aszendent/MC)", default=False)
    is_optional_body = models.BooleanField("Optionaler Zusatzpunkt (Chiron/Pholus/Lilith)", default=False)

    class Meta:
        verbose_name = "Planet"
        verbose_name_plural = "Planeten"
        ordering = ["id"]

    def __str__(self):
        return self.name_de


class House(models.Model):
    number = models.PositiveSmallIntegerField("Hausnummer", unique=True)
    name_de = models.CharField("Name", max_length=100)
    short_meaning = models.CharField("Kurzbedeutung", max_length=200, blank=True)

    class Meta:
        verbose_name = "Haus"
        verbose_name_plural = "Häuser"
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. Haus – {self.name_de}"


class ThemenBild(StoredImage):
    """Feste Bilder, die unabhaengig vom Planeten immer am selben Abschnitt
    erscheinen (bei Sonne/Aszendent/Mond identisch verwendet, also NICHT
    nach Planet unterschieden) - aktuell nur Liebe und Kind."""

    TOPICS = [
        ("liebe", "Liebe/Partnerschaft"),
        ("kind", "Kindheit"),
    ]

    topic = models.CharField("Thema", max_length=20, choices=TOPICS, unique=True)

    class Meta:
        verbose_name = "Themenbild"
        verbose_name_plural = "Themenbilder"

    def __str__(self):
        return self.get_topic_display()


class ShortDescription(TrackedText):
    """Kurzbeschreibung mit eingebettetem Zeichen-Symbol - bewusst EIN Feld
    pro Planet+Zeichen, unabhaengig von der (pro Planet unterschiedlichen)
    Langbeschreibungs-Struktur in InterpretationText."""

    planet = models.ForeignKey(Planet, verbose_name="Planet", on_delete=models.PROTECT)
    sign = models.ForeignKey(ZodiacSign, verbose_name="Zeichen", on_delete=models.PROTECT)
    body = models.TextField("Text")

    class Meta:
        verbose_name = "Kurzbeschreibung"
        verbose_name_plural = "Kurzbeschreibungen"
        unique_together = ("planet", "sign")

    def __str__(self):
        return f"Kurzbeschreibung {self.planet} in {self.sign}"


class PlanetHouseText(TrackedText):
    """Text je Planet+Haus, UNABHAENGIG vom Zeichen (z. B. "Neptun im 1.
    Haus") - andere Achse als InterpretationText (Planet+Zeichen) und
    HausherrAszendentText (Aszendentzeichen+Haus, mit Herrscherplanet-
    Bezug). Beim Report wird pro Chart nur der zur tatsaechlich berechneten
    Hausposition passende Text gezogen (z. B. chart.sun_house)."""

    planet = models.ForeignKey(Planet, verbose_name="Planet", on_delete=models.PROTECT)
    house = models.ForeignKey(House, verbose_name="Haus", on_delete=models.PROTECT)
    body = models.TextField("Text")

    class Meta:
        verbose_name = "Planet-im-Haus-Text"
        verbose_name_plural = "Planet-im-Haus-Texte"
        unique_together = ("planet", "house")

    def __str__(self):
        return f"{self.planet} im {self.house}"


class InterpretationText(TrackedText):
    """Lange Beschreibung je Planet/Zeichen/Textart.

    Zulaessige text_type-Werte sind PRO PLANET unterschiedlich (siehe
    clean() und VALID_TYPES_BY_PLANET_KEY):
      Sonne:      grund, konstruktiv, problematisch, gegenteil, beziehung,
                  beruf, kindheit, aufgaben_karma, entsprechungen   (9)
      Aszendent:  grund, beziehung, beruf, kindheit                 (4)
      Mond:       erfuellt, unerfuellt, beziehung, psychologisches,
                  kindheit, gesundheit                              (6)

    Kein house-Feld (Haus-abhaengiger Inhalt laeuft ausschliesslich ueber
    HausherrAszendentText) und kein heilstein_intro mehr (Phase-7-Backlog)."""

    TEXT_TYPES = [
        ("grund", "Allgemeine Beschreibung (Grundtext)"),
        ("konstruktiv", "Der konstruktive [Zeichen]"),
        ("problematisch", "Der problematische [Zeichen]"),
        ("gegenteil", "Das Gegenteil der Eigenschaften"),
        ("beziehung", "Freundschaft/Partnerschaft/Liebe"),
        ("beruf", "Beruf"),
        ("kindheit", "Kindheit"),
        ("aufgaben_karma", "Aufgaben/Karma/Gesundheit"),
        ("entsprechungen", "Entsprechungen"),
        ("erfuellt", "Die erfüllte Seite"),
        ("unerfuellt", "Die unerfüllte Seite"),
        ("psychologisches", "Psychologisches"),
        ("gesundheit", "Gesundheit (Kurzform)"),
    ]

    # Ueber Planet.key statt Planet.name_de (Anzeigename) verzweigt - der
    # Schluessel ist stabil, der Anzeigename koennte sich aendern.
    VALID_TYPES_BY_PLANET_KEY = {
        "sonne": {"grund", "konstruktiv", "problematisch", "gegenteil",
                  "beziehung", "beruf", "kindheit", "aufgaben_karma", "entsprechungen"},
        "aszendent": {"grund", "beziehung", "beruf", "kindheit"},
        "mond": {"erfuellt", "unerfuellt", "beziehung", "psychologisches",
                 "kindheit", "gesundheit"},
    }

    planet = models.ForeignKey(Planet, verbose_name="Planet", on_delete=models.PROTECT)
    sign = models.ForeignKey(ZodiacSign, verbose_name="Zeichen", on_delete=models.PROTECT)
    text_type = models.CharField("Textart", max_length=20, choices=TEXT_TYPES)
    # Freitext statt automatisch aus TEXT_TYPES abgeleitet: "Der konstruktive
    # [Zeichen]" laesst sich nicht automatisch korrekt befuellen (Artikel/
    # Adjektivendung sind je nach grammatikalischem Geschlecht des Zeichens
    # unterschiedlich, z.B. "Der konstruktive Widder" vs. "Die konstruktive
    # Waage") - die Redaktion traegt die fertige Ueberschrift direkt ein.
    # text_type bleibt trotzdem bestehen (Zuordnung/Reihenfolge/Validierung).
    heading = models.CharField(
        "Überschrift", max_length=200, blank=True,
        help_text="Erscheint als Zwischenüberschrift im Report. Leer lassen für keine Überschrift.",
    )
    body = models.TextField("Text")
    # Interne Notiz zu Inspirationsquellen - NICHT die Vorlage selbst, siehe
    # Umsetzungsplan Phase 0 (keine Uebernahme/Paraphrase fremder Texte).
    source_notes = models.TextField("Quellen-Notiz (intern)", blank=True)

    class Meta:
        verbose_name = "Auswertungstext"
        verbose_name_plural = "Auswertungstexte"
        unique_together = ("planet", "sign", "text_type")

    def clean(self):
        valid = self.VALID_TYPES_BY_PLANET_KEY.get(self.planet.key, set())
        if self.text_type not in valid:
            raise ValidationError(
                f"Textart „{self.text_type}“ ist für Planet „{self.planet}“ nicht zulässig. "
                f"Erlaubt: {sorted(valid) or 'keine (nicht Sonne/Aszendent/Mond)'}"
            )

    def __str__(self):
        return f"{self.planet} in {self.sign} – {self.get_text_type_display()}"


class SonneMondKombiText(TrackedText):
    """EIN Datensatz je Sonnenzeichen+Mondzeichen (144 insgesamt). Die
    Formelzeile ("Sonne in Widder = Sonne/Mars") wird NICHT gespeichert,
    sondern zur Laufzeit aus sign_sonne.ruler_planet / sign_mond.ruler_planet
    erzeugt."""

    sign_sonne = models.ForeignKey(ZodiacSign, verbose_name="Sonnenzeichen", on_delete=models.PROTECT, related_name="+")
    sign_mond = models.ForeignKey(ZodiacSign, verbose_name="Mondzeichen", on_delete=models.PROTECT, related_name="+")

    kombi_text = models.TextField("Einleitungstext", help_text="Freier Fließtext, Einleitung des Kapitels")

    sonne_charakter = models.TextField("Sonne: Charakter")
    sonne_lernt = models.TextField("Sonne: Lernt")
    sonne_muss = models.TextField("Sonne: Muss")
    sonne_liebe = models.TextField("Sonne: Liebe")
    sonne_astrologik = models.TextField("Sonne: Astrologik")

    mond_charakter = models.TextField("Mond: Charakter")
    mond_lernt = models.TextField("Mond: Lernt")
    mond_muss = models.TextField("Mond: Muss")
    mond_liebe = models.TextField("Mond: Liebe")
    mond_astrologik = models.TextField("Mond: Astrologik")

    class Meta:
        verbose_name = "Sonne-Mond-Kombination"
        verbose_name_plural = "Sonne-Mond-Kombinationen"
        unique_together = ("sign_sonne", "sign_mond")

    def __str__(self):
        return f"Sonne {self.sign_sonne} + Mond {self.sign_mond}"


class SonneAszendentKombiText(TrackedText):
    """EIN Datensatz je Sonnenzeichen+Aszendentzeichen (144 insgesamt).
    body enthaelt Kurztext inkl. Chance/Herausforderung als ein
    zusammenhaengender Block - KEINE Gegenueberstellungs-Tabelle wie bei
    Sonne-Mond."""

    sign_sonne = models.ForeignKey(ZodiacSign, verbose_name="Sonnenzeichen", on_delete=models.PROTECT, related_name="+")
    sign_aszendent = models.ForeignKey(ZodiacSign, verbose_name="Aszendentzeichen", on_delete=models.PROTECT, related_name="+")
    body = models.TextField("Text", help_text="Kompletter Block: Kurztext + Chance/Herausforderung")

    class Meta:
        verbose_name = "Sonne-Aszendent-Kombination"
        verbose_name_plural = "Sonne-Aszendent-Kombinationen"
        unique_together = ("sign_sonne", "sign_aszendent")

    def __str__(self):
        return f"Sonne {self.sign_sonne} + Aszendent {self.sign_aszendent}"


class HausherrAszendentText(TrackedText):
    """EIN Datensatz je Aszendentzeichen+Haus (144 insgesamt). Haengt NICHT
    vom Sonnenzeichen ab - deshalb eigenes Modell, getrennt von
    SonneAszendentKombiText. body enthaelt den kompletten Text (Titel,
    Formel, Einleitungssatz, Charakterabsatz) als ein Block."""

    sign_aszendent = models.ForeignKey(ZodiacSign, verbose_name="Aszendentzeichen", on_delete=models.PROTECT, related_name="+")
    house = models.ForeignKey(House, verbose_name="Haus", on_delete=models.PROTECT)
    body = models.TextField("Text", help_text="Kompletter Block: Titel + Formel + Einleitung + Charakterabsatz")

    class Meta:
        verbose_name = "Hausherr-Aszendent-Text"
        verbose_name_plural = "Hausherr-Aszendent-Texte"
        unique_together = ("sign_aszendent", "house")

    @property
    def ruler_planet(self):
        """Wird ueber sign_aszendent.ruler_planet aufgeloest, nicht separat
        gespeichert."""
        return self.sign_aszendent.ruler_planet

    def __str__(self):
        return f"Hausherr Aszendent {self.sign_aszendent} im {self.house}. Haus"


class GemstoneCorrespondence(models.Model):
    """BACKLOG (Phase 7), unveraendert - Verknuepfung zur bestehenden
    Heilstein-Lexikon-DB (nur Referenz, kein echter FK)."""

    ROLES = [
        ("hauptstein", "Hauptstein"),
        ("ergaenzungsstein", "Ergänzungsstein"),
    ]

    sign = models.ForeignKey(ZodiacSign, verbose_name="Zeichen", on_delete=models.PROTECT, null=True, blank=True)
    planet = models.ForeignKey(Planet, verbose_name="Planet", on_delete=models.PROTECT, null=True, blank=True)
    heilstein_ref = models.CharField("Heilstein-Referenz", max_length=100)
    role = models.CharField("Rolle", max_length=50, choices=ROLES)
    note = models.TextField("Hinweis", blank=True)

    class Meta:
        verbose_name = "Heilstein-Zuordnung"
        verbose_name_plural = "Heilstein-Zuordnungen"

    def __str__(self):
        return f"{self.heilstein_ref} ({self.get_role_display()})"


class BirthChart(models.Model):
    HOUSE_SYSTEMS = [
        ("placidus", "Placidus"),
        ("koch", "Koch"),
        ("equal", "Equal"),
        ("whole_sign", "Whole Sign"),
    ]

    label = models.CharField("Bezeichnung", max_length=150, blank=True)
    birth_date = models.DateField("Geburtsdatum")
    birth_time = models.TimeField("Geburtszeit", null=True, blank=True)
    birth_place_raw = models.CharField("Geburtsort", max_length=200)
    # GeoNames-ID des gewaehlten Orts (falls per Autocomplete gewaehlt) -
    # erspart bei erneuter Auswahl desselben Orts eine neue Geocoding-Anfrage.
    geonameid = models.CharField("GeoNames-ID", max_length=20, blank=True)
    birth_lat = models.FloatField("Breitengrad", null=True, blank=True)
    birth_lon = models.FloatField("Längengrad", null=True, blank=True)
    birth_timezone = models.CharField("Zeitzone", max_length=64, blank=True)
    house_system = models.CharField("Häusersystem", max_length=20, choices=HOUSE_SYSTEMS, default="placidus")
    include_chiron = models.BooleanField("Chiron einbeziehen", default=True)
    include_pholus = models.BooleanField("Pholus einbeziehen", default=True)
    include_lilith = models.BooleanField("Lilith einbeziehen", default=True)

    sun_sign = models.ForeignKey(ZodiacSign, verbose_name="Sonnenzeichen", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    sun_house = models.ForeignKey(House, verbose_name="Sonnenhaus", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    moon_sign = models.ForeignKey(ZodiacSign, verbose_name="Mondzeichen", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    moon_house = models.ForeignKey(House, verbose_name="Mondhaus", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    ascendant_sign = models.ForeignKey(ZodiacSign, verbose_name="Aszendent", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    mc_sign = models.ForeignKey(ZodiacSign, verbose_name="Medium Coeli (MC)", on_delete=models.PROTECT, related_name="+", null=True, blank=True)

    # Vollstaendiger Ephemeriden-Output (alle Planeten/Haeuser/Aspekte) - die
    # obigen FK-Felder sind nur ein schneller Zugriff auf die drei
    # Kernpositionen fuer Reports, nicht die alleinige Datenquelle.
    raw_positions = models.JSONField("Rohdaten (Ephemeride)", default=dict, blank=True)
    computed_at = models.DateTimeField("Berechnet am", auto_now_add=True)

    class Meta:
        verbose_name = "Geburtshoroskop"
        verbose_name_plural = "Geburtshoroskope"
        ordering = ["-computed_at"]

    def __str__(self):
        return self.label or f"Horoskop vom {self.birth_date}"


class GeocodeCache(models.Model):
    """Vermeidet wiederholte GeoNames-Anfragen fuer denselben Ort (z. B.
    "Bad Kreuznach" kommt bei mehreren Horoskopen wieder vor)."""

    query = models.CharField("Suchanfrage", max_length=200, unique=True)
    geonameid = models.CharField("GeoNames-ID", max_length=20, blank=True)
    name = models.CharField("Ortsname", max_length=200, blank=True)
    country = models.CharField("Land", max_length=100, blank=True)
    lat = models.FloatField("Breitengrad")
    lon = models.FloatField("Längengrad")
    timezone = models.CharField("Zeitzone", max_length=64, blank=True)
    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    class Meta:
        verbose_name = "Geocode-Cache-Eintrag"
        verbose_name_plural = "Geocode-Cache-Einträge"

    def __str__(self):
        return f"{self.name or self.query} ({self.lat}, {self.lon})"


class GeneratedReport(models.Model):
    FORMATS = [("pdf", "PDF"), ("docx", "DOCX")]

    chart = models.ForeignKey(BirthChart, verbose_name="Geburtshoroskop", on_delete=models.CASCADE, related_name="reports")
    order_reference = models.CharField("Bestellreferenz", max_length=100, blank=True)
    format = models.CharField("Format", max_length=10, choices=FORMATS)
    file = models.FileField("Datei", upload_to="astro_reports/%Y/%m/")
    chart_wheel_svg = models.FileField("Horoskoprad (SVG)", upload_to="astro_charts/%Y/%m/", null=True, blank=True)
    generated_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    class Meta:
        verbose_name = "Erstellter Report"
        verbose_name_plural = "Erstellte Reports"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Report {self.pk} – {self.chart}"


class ReportBranding(StoredImage):
    """Singleton - globale Report-Assets, die nicht pro Zeichen/Planet
    variieren (aktuell nur der Deckblatt-Hintergrund). Immer pk=1, siehe
    save()/delete() - dasselbe Singleton-Muster wie CompanyProfile in
    settings_hub. Blob statt Datei in media/, damit astro.db wie
    lexikon.sqlite3 eigenstaendig/portabel bleibt, unabhaengig vom
    media-Ordner der App."""

    class Meta:
        verbose_name = "Report-Branding"
        verbose_name_plural = "Report-Branding"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return "Report-Branding"
