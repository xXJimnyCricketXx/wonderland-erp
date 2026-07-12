from django.db import models


class MaterialCategory(models.Model):
    """The official VerpackG/LUCID material categories (Glas, Pappe/Papier/
    Karton, Eisenmetalle, ...) - one shared €/kg licensing rate per category,
    read off the yearly Grüner Punkt invoice, used by every PackagingType via
    PackagingTypeMaterial rather than duplicated per packaging type."""

    name = models.CharField("Name", max_length=100, unique=True)
    price_per_kg = models.DecimalField("Preis (€/kg)", max_digits=8, decimal_places=4, default=0)
    # LUCID's own numeric material code (e.g. 20000 = Papier/Pappe/Karton) -
    # lets an imported Datenmeldung-XML's <MaterialCode> be matched back to
    # our own category instead of staying an opaque number.
    lucid_material_code = models.CharField("LUCID-Materialcode", max_length=10, blank=True)

    class Meta:
        verbose_name = "Materialkategorie"
        verbose_name_plural = "Materialkategorien"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PackagingType(models.Model):
    """LUCID/Verpackungsregister reference data - one row per distinct
    packing profile (e.g. "DHL Paket S ohne Füllmaterial" vs "... mit
    Kunststoff-Füllmaterial" are separate rows since their material makeup
    differs). Yearly totals are computed from Order.package_type usage, not
    stored here."""

    name = models.CharField("Bezeichnung", max_length=100, unique=True)
    description = models.CharField("Beschreibung", max_length=255, blank=True)
    dimensions = models.CharField("Maße", max_length=100, blank=True)
    valid_from = models.DateField("Gültig ab", blank=True, null=True)

    class Meta:
        verbose_name = "Verpackungsart"
        verbose_name_plural = "Verpackungsarten"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PackagingTypeMaterial(models.Model):
    """Per-category material weight for one PackagingType - the mapping
    table that keeps the material list extensible without a schema change
    (see also ReferenceOption for the same "stays extensible" pattern)."""

    packaging_type = models.ForeignKey(
        PackagingType, verbose_name="Verpackungsart", on_delete=models.CASCADE, related_name="materials"
    )
    material_category = models.ForeignKey(
        MaterialCategory, verbose_name="Materialkategorie", on_delete=models.CASCADE
    )
    kg_per_unit = models.DecimalField("kg pro Stück", max_digits=6, decimal_places=4, default=0)

    class Meta:
        verbose_name = "Verpackungsart-Material"
        verbose_name_plural = "Verpackungsart-Materialien"
        unique_together = [["packaging_type", "material_category"]]
        ordering = ["packaging_type", "material_category"]

    def __str__(self):
        return f"{self.packaging_type} - {self.material_category}"


class ShippingOption(models.Model):
    carrier = models.CharField("Anbieter", max_length=100)
    description = models.CharField("Beschreibung", max_length=255)
    use_case = models.CharField("Anwendung", max_length=255, blank=True)
    # Kept as text - not always a clean number (e.g. "X (+4,00)" for a
    # tracking surcharge on top of a base rate).
    price_note = models.CharField("Preis", max_length=100, blank=True)
    payment_method = models.CharField("Bezahlen", max_length=50, blank=True)
    requires_tracking_number = models.BooleanField("Sendungsnummer nötig", default=False)
    is_international = models.BooleanField("International", default=False)
    valid_from = models.DateField("Gültig ab", blank=True, null=True)

    class Meta:
        verbose_name = "Versandoption"
        verbose_name_plural = "Versandoptionen"
        ordering = ["carrier", "description"]

    def __str__(self):
        return f"{self.carrier} - {self.description}"


class CustomsTariffCode(models.Model):
    code = models.CharField("Zolltarifnummer", max_length=20, unique=True)
    definition = models.CharField("Definition", max_length=255)
    description = models.CharField("Beschreibung", max_length=255, blank=True)

    class Meta:
        verbose_name = "Zolltarifnummer"
        verbose_name_plural = "Zolltarifnummern"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.definition}"


def packaging_license_document_path(instance, filename):
    return f"documents/verpackungslizenz/{instance.doc_type}/{filename}"


class PackagingLicenseDocument(models.Model):
    """Yearly paperwork from the LUCID/Grüner Punkt packaging-license
    contract - contract sheet, invoices, participation confirmations,
    environmental certificates. No matching business record exists to
    attach these to (unlike Order/Expense), hence its own small model."""

    DOC_TYPE_RECHNUNG = "rechnung"
    DOC_TYPE_VERTRAGSBLATT = "vertragsblatt"
    DOC_TYPE_TEILNAHMEBESTAETIGUNG = "teilnahmebestaetigung"
    DOC_TYPE_UMWELTZERTIFIKAT = "umweltzertifikat"
    DOC_TYPE_MITTEILUNG = "mitteilung"
    DOC_TYPE_CHOICES = [
        (DOC_TYPE_RECHNUNG, "Rechnung"),
        (DOC_TYPE_VERTRAGSBLATT, "Vertragsblatt"),
        (DOC_TYPE_TEILNAHMEBESTAETIGUNG, "Teilnahmebestätigung"),
        (DOC_TYPE_UMWELTZERTIFIKAT, "Umweltzertifikat"),
        (DOC_TYPE_MITTEILUNG, "Mitteilung/Sonstiges"),
    ]

    year = models.PositiveIntegerField("Jahr")
    doc_type = models.CharField("Dokumenttyp", max_length=30, choices=DOC_TYPE_CHOICES)
    file = models.FileField("Datei", upload_to=packaging_license_document_path)
    uploaded_at = models.DateTimeField("Hochgeladen am", auto_now_add=True)

    class Meta:
        verbose_name = "Verpackungslizenz-Dokument"
        verbose_name_plural = "Verpackungslizenz-Dokumente"
        ordering = ["-year", "doc_type"]

    def __str__(self):
        return f"{self.get_doc_type_display()} {self.year}"


class PackagingLicenseSubmission(models.Model):
    """Tracks whether the two recurring DSD/Grüner Punkt deadlines were
    actually submitted, per year - so the reminder notification can stop
    nagging once it's done instead of firing on a bare calendar date
    (see AGB Beteiligung §5/§8, testdata/ContractSheet_5695332.pdf)."""

    TYPE_JAHRESABSCHLUSSMELDUNG = "jahresabschlussmeldung"
    TYPE_PLANMENGENANPASSUNG = "planmengenanpassung"
    TYPE_LUCID_MELDUNG = "lucid_meldung"
    TYPE_CHOICES = [
        (TYPE_JAHRESABSCHLUSSMELDUNG, "Jahresabschlussmeldung"),
        (TYPE_PLANMENGENANPASSUNG, "Planmengenanpassung"),
        (TYPE_LUCID_MELDUNG, "LUCID-Datenmeldung"),
    ]

    year = models.PositiveIntegerField("Jahr")
    submission_type = models.CharField("Meldungsart", max_length=30, choices=TYPE_CHOICES)
    # Deliberately just a flag, no date - a "submitted on" date can't be
    # reliably reconstructed for older/backfilled entries, and the
    # notification logic only ever needs today > due_date && not submitted.
    submitted = models.BooleanField("Abgegeben", default=False)

    class Meta:
        verbose_name = "Verpackungslizenz-Meldung"
        verbose_name_plural = "Verpackungslizenz-Meldungen"
        unique_together = [["year", "submission_type"]]
        ordering = ["-year", "submission_type"]

    def __str__(self):
        return f"{self.get_submission_type_display()} {self.year}"

    @property
    def due_date(self):
        import datetime
        if self.submission_type == self.TYPE_JAHRESABSCHLUSSMELDUNG:
            # Reports the PRIOR year's actual quantities, due end of Q1.
            return datetime.date(self.year + 1, 3, 31)
        if self.submission_type == self.TYPE_LUCID_MELDUNG:
            # LUCID's own Jahresabschlussmengenmeldung is correctable until
            # 15.05. of the following year, per the LUCID FAQ text - taking
            # that as the effective deadline (separate from, and later than,
            # the 31.03. Grüner-Punkt/DSD deadline above, since these are two
            # different recipients for the same underlying yearly figures).
            return datetime.date(self.year + 1, 5, 15)
        return datetime.date(self.year, 8, 31)


class PackagingLicenseDataReport(models.Model):
    """One Datenmeldung - either imported from a LUCID-format XML file, or
    entered manually (Der Grüne Punkt only lets you re-download old filings
    as PDF, not XML, per the user - so manual entry is the only option for
    backfilling those). Both LUCID and Der Grüne Punkt hand out the same XML
    interchange format when it IS available (a Grüne-Punkt Datenmeldung can
    be re-uploaded to LUCID as-is), so one model covers both, distinguished
    by `recipient`. XML parsed by `apps/data_import/packaging_license_import.py`."""

    RECIPIENT_LUCID = "lucid"
    RECIPIENT_GRUENER_PUNKT = "gruener_punkt"
    RECIPIENT_CHOICES = [
        (RECIPIENT_LUCID, "LUCID"),
        (RECIPIENT_GRUENER_PUNKT, "Der Grüne Punkt"),
    ]

    TYPE_UNTERJAEHRIG = "unterjaehrige_mengenmeldung"
    TYPE_JAHRESABSCHLUSS = "jahresabschlussmengenmeldung"
    TYPE_INITIALE_PLANMENGE = "initiale_planmengenmeldung"
    TYPE_NACHTRAG = "nachtragsmengenmeldung"
    TYPE_SONSTIGE = "sonstige"
    TYPE_CHOICES = [
        (TYPE_UNTERJAEHRIG, "Unterjährige Mengenmeldung"),
        (TYPE_JAHRESABSCHLUSS, "Jahresabschlussmengenmeldung"),
        (TYPE_INITIALE_PLANMENGE, "Initiale Planmengenmeldung"),
        (TYPE_NACHTRAG, "Nachtragsmengenmeldung"),
        (TYPE_SONSTIGE, "Sonstige/Unbekannt"),
    ]
    # "Abgegebene Datenmeldungen" vs "Abgegebene Nachtragsmengenmeldungen /
    # Planmengenanpassung" - which of the two Infothek tables a report shows
    # up in, confirmed against the LUCID portal's own grouping.
    NACHTRAG_TYPES = [TYPE_NACHTRAG, TYPE_INITIALE_PLANMENGE]

    # Confirmed via the LUCID portal (user-provided screenshots/mapping):
    CODE_TO_TYPE = {
        "HMM1": TYPE_UNTERJAEHRIG,
        "HJM1": TYPE_JAHRESABSCHLUSS,
    }

    recipient = models.CharField("Empfänger", max_length=20, choices=RECIPIENT_CHOICES)
    report_type = models.CharField(
        "Meldeart", max_length=30, choices=TYPE_CHOICES, default=TYPE_SONSTIGE
    )
    # Raw <TypeOfReportCode> value (e.g. "HMM1") from an XML import - blank
    # for manually-entered reports, which don't have one.
    type_of_report_code = models.CharField("Meldungsart-Code (XML)", max_length=20, blank=True)
    reporting_period_from = models.DateField("Meldezeitraum von")
    reporting_period_to = models.DateField("Meldezeitraum bis")
    system_operator_id = models.CharField("Systembeteiligungs-ID", max_length=50, blank=True)
    source_file = models.FileField(
        "Quelldatei (XML oder PDF)", upload_to="documents/verpackungslizenz/xml/", blank=True, null=True
    )
    imported_at = models.DateTimeField("Erfasst am", auto_now_add=True)

    class Meta:
        verbose_name = "Verpackungslizenz-Datenmeldung"
        verbose_name_plural = "Verpackungslizenz-Datenmeldungen"
        ordering = ["-reporting_period_from"]

    def __str__(self):
        return f"{self.get_recipient_display()} {self.reporting_period_from:%Y} ({self.get_report_type_display()})"

    @property
    def total_mass_kg(self):
        return sum((line.mass_kg for line in self.materials.all()), 0)


class PackagingLicenseDataReportMaterial(models.Model):
    """One material-category line (kg) within a Datenmeldung - from an
    imported XML's <Material> element, or entered by hand."""

    report = models.ForeignKey(
        PackagingLicenseDataReport, verbose_name="Datenmeldung", on_delete=models.CASCADE, related_name="materials"
    )
    material_category = models.ForeignKey(
        MaterialCategory, verbose_name="Materialkategorie", on_delete=models.SET_NULL, null=True, blank=True
    )
    # Raw code kept even when it DID match a MaterialCategory, so an
    # unrecognized code isn't silently dropped from the record - blank for
    # manually-entered lines (those are created directly against a category).
    material_code = models.CharField("LUCID-Materialcode", max_length=10, blank=True)
    # Confirmed via the LUCID portal ("Mengenangaben in kg mit 3
    # Nachkommastellen") - same unit as the internal Rechner.
    mass_kg = models.DecimalField("Menge (kg)", max_digits=10, decimal_places=3, default=0)

    class Meta:
        verbose_name = "Datenmeldung-Material"
        verbose_name_plural = "Datenmeldung-Materialien"
        ordering = ["material_code"]

    def __str__(self):
        return f"{self.material_category or self.material_code}: {self.mass_kg} kg"
