"""LUCID-format 'Datenmeldung' XML -> PackagingLicenseDataReport (+ line
items). Both LUCID and Der Grüne Punkt hand out the same interchange format
(a Grüne-Punkt Datenmeldung can be re-uploaded to LUCID as-is), so one parser
covers both - `recipient` is picked by the user on the upload form, not
derived from the file itself, since the XML doesn't say which portal it's
for.

<TypeOfReportCode>HMM1</TypeOfReportCode> is confirmed (via the LUCID portal's
own "Datenmeldung ansehen" page) to mean "Unterjährige Mengenmeldung" - see
PackagingLicenseDataReport.CODE_TO_TYPE. Any other/unknown code still imports
cleanly, just filed under "Sonstige/Unbekannt" until its mapping is confirmed
too."""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation

from knowledge.models import MaterialCategory, PackagingLicenseDataReport, PackagingLicenseDataReportMaterial


class PackagingLicenseImportError(Exception):
    pass


def _parse_date(raw):
    return datetime.strptime(raw.strip(), "%Y-%m-%d").date()


def _parse_mass(raw):
    # LUCID exports German-decimal-comma numbers (e.g. "0,476").
    try:
        return Decimal(raw.strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        return Decimal("0")


def import_packaging_license_xml(file_obj, recipient):
    try:
        tree = ET.parse(file_obj)
    except ET.ParseError as exc:
        raise PackagingLicenseImportError(f"Datei ist kein gültiges XML: {exc}") from exc

    root = tree.getroot()

    type_of_report_code = (root.findtext("TypeOfReportCode") or "").strip()
    period_from_raw = root.findtext("ReportingPeriodFrom")
    period_to_raw = root.findtext("ReportingPeriodTo")
    if not type_of_report_code or not period_from_raw or not period_to_raw:
        raise PackagingLicenseImportError(
            "XML fehlt eines der Pflichtfelder TypeOfReportCode/ReportingPeriodFrom/ReportingPeriodTo."
        )

    operator = root.find("./ListOfSystemOperators/SystemOperator")
    system_operator_id = (operator.findtext("SystemOperatorID") or "").strip() if operator is not None else ""

    categories_by_code = {
        c.lucid_material_code: c for c in MaterialCategory.objects.exclude(lucid_material_code="")
    }

    file_obj.seek(0)
    report = PackagingLicenseDataReport.objects.create(
        recipient=recipient,
        report_type=PackagingLicenseDataReport.CODE_TO_TYPE.get(
            type_of_report_code, PackagingLicenseDataReport.TYPE_SONSTIGE
        ),
        type_of_report_code=type_of_report_code,
        reporting_period_from=_parse_date(period_from_raw),
        reporting_period_to=_parse_date(period_to_raw),
        system_operator_id=system_operator_id,
        source_file=file_obj,
    )

    materials_created = 0
    if operator is not None:
        for material_el in operator.findall("./ListOfMaterials/Material"):
            code = (material_el.findtext("MaterialCode") or "").strip()
            mass = _parse_mass(material_el.findtext("Mass") or "0")
            PackagingLicenseDataReportMaterial.objects.create(
                report=report,
                material_code=code,
                material_category=categories_by_code.get(code),
                mass_kg=mass,
            )
            materials_created += 1

    return report, materials_created
