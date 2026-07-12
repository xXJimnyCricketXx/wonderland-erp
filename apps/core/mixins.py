class BackModalMixin:
    """Adds `back_modal_id` to context from the `zurueck_zu` query param, so
    a shared detail-modal partial can render an optional "Zurück"-button.

    Used for the "quick-view stacked on another modal" pattern (e.g. Artikel
    opened from within an open Bestellung): Bootstrap 5 doesn't officially
    support two modals open at once, so instead of faking a real stack, the
    trigger link closes modal A and opens modal B (data-bs-dismiss +
    data-bs-toggle together, Bootstrap's own documented "Modal Toggle"
    pattern) and passes ?zurueck_zu=<id of A> along with it. Modal B's
    footer then shows a "Zurück"-button that closes B and reopens A -  A's
    content div still has its previously-loaded HTML, so no refetch needed.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_modal_id"] = self.request.GET.get("zurueck_zu")
        return context
