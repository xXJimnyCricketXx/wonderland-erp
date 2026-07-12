from django.db.models import F, Q
from django.urls import reverse

from core.notifications import Notification, color_for_level

from .models import Article


def get_stock_notifications(request):
    """One notification per top-level article that (or whose variants) is
    low on stock or sold out - not dismissible, since it reflects a live
    state (see the "Lagerwarnung wegklicken?" decision): it just stops
    appearing on its own once the stock is topped back up, rather than
    needing to be acknowledged like a one-off appointment reminder."""
    if not request.user.is_authenticated:
        return []

    # No Soll-Bestand set -> no warning at all, same rule as Article._is_low_stock.
    problem_units = Article.objects.filter(
        is_archived=False, is_active=True,
        minimum_stock_quantity__isnull=False, stock_quantity__lt=F("minimum_stock_quantity"),
    ).select_related("parent_article")

    # Variants roll up into their parent's notification instead of getting
    # their own - a listing with 5 low-stock variants should surface once,
    # not five times, same as the existing needs_restock badge on the list.
    by_parent = {}
    for unit in problem_units:
        parent = unit.parent_article or unit
        level = "danger" if unit.stock_quantity == 0 else "warning"
        entry = by_parent.setdefault(parent.pk, {"parent": parent, "level": None, "unit": None})
        if entry["level"] != "danger":
            entry["level"] = level
            entry["unit"] = unit

    notifications = []
    for entry in by_parent.values():
        parent, level, unit = entry["parent"], entry["level"], entry["unit"]
        bg, fg = color_for_level(level)
        label = unit.variant_label or parent.title
        if level == "danger":
            header = "Ausverkauft"
            body = f"{label} ist ausverkauft (Bestand: 0)"
        else:
            header = "Lagerwarnung"
            body = f"{label}: Bestand {unit.stock_quantity} unter Soll-Bestand {unit.minimum_stock_quantity}"
        # catalog:detail renders a bare HTMX modal-content fragment, not a
        # full page - not something to link to directly. The list, filtered
        # down to this article's SKU, is what a plain navigation should go to.
        search_term = parent.sku or parent.title
        notifications.append(Notification(
            header=header,
            subtitle=parent.sku or "",
            body=body,
            bg_color=bg,
            fg_color=fg,
            detail_url=f"{reverse('catalog:list')}?q={search_term}",
            dismiss_url="",
        ))

    notifications.sort(key=lambda n: n.header != "Ausverkauft")
    return notifications
