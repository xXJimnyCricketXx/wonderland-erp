"""Deterministic pastel colors per Termin-Typ. Colors are assigned by the
type's position in the Referenzdaten list (stable across restarts, unlike
Python's randomized str hash) rather than a color field on the shared
ReferenceOption model, which every other category also uses."""

PALETTE = [
    ("#C7F5D9", "#0B4121"),
    ("#CFE0FC", "#0A47A9"),
    ("#EBCDFE", "#6E02B1"),
    ("#FDD8DE", "#790619"),
    ("#FFF3C4", "#7A5B00"),
    ("#D7ECEF", "#0B4B57"),
]
FALLBACK = ("#E9ECEF", "#495057")


def build_color_map(ordered_type_values):
    """ordered_type_values: list of ReferenceOption.value in display order."""
    return {
        value: PALETTE[i % len(PALETTE)]
        for i, value in enumerate(ordered_type_values)
    }


def annotate_colors(appointments, color_map):
    for appt in appointments:
        bg, fg = color_map.get(appt.event_type, FALLBACK)
        appt.bg_color = bg
        appt.fg_color = fg
    return appointments
