from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

from core.htmx_utils import htmx_redirect
from core.mixins import BackModalMixin
from core.models import ReferenceOption
from core.sorting import resolve_sort

from .forms import OrderForm, OrderItemFormSet
from .models import Order, Review


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    ALLOWED_SORT_FIELDS = {
        "order_id", "etsy_order_number", "customer__last_name", "customer__first_name",
        "sale_date", "number_of_items", "order_total", "status",
    }

    def get_queryset(self):
        qs = Order.objects.filter(is_archived=False).select_related("customer")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(order_id__icontains=query)
                | Q(etsy_order_number__icontains=query)
                | Q(customer__first_name__icontains=query)
                | Q(customer__last_name__icontains=query)
                | Q(buyer_username__icontains=query)
                | Q(tracking_number__icontains=query)
            )

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        order_type = self.request.GET.get("order_type")
        if order_type:
            qs = qs.filter(order_type=order_type)

        sort = resolve_sort(self.request, self.ALLOWED_SORT_FIELDS, "-sale_date")
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aus Referenzdaten, nicht aus den vorhandenen Bestellungen abgeleitet -
        # sonst fehlen konfigurierte Werte im Filter, solange noch keine
        # Bestellung diesen Status/Typ trägt.
        context["statuses"] = ReferenceOption.objects.filter(category="order_status").order_by("order", "value")
        context["order_types"] = ReferenceOption.objects.filter(category="order_type").order_by("order", "value")
        context["query"] = self.request.GET.get("q", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_order_type"] = self.request.GET.get("order_type", "")
        context["trash_count"] = Order.objects.filter(is_archived=True).count()
        return context


class OrderDetailModalView(BackModalMixin, LoginRequiredMixin, DetailView):
    """Read-only 'Bestellschein' shown by the eye icon - its footer links
    into OrderModalView for editing."""

    model = Order
    template_name = "orders/_order_detail_modal.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_items"] = self.object.items.select_related("article").all()
        context["reviews"] = self.object.reviews.all()
        return context


class OrderModalView(LoginRequiredMixin, View):
    """Create/update in one view (not two CBVs) because the OrderItem
    inline formset (Positionen: Artikel/SKU nachtragen) needs to be
    validated together with the main form before either is saved - same
    pattern as SupplierModalView/WishlistItemModalView."""

    template_name = "orders/_order_modal.html"

    def _get_instance(self, pk):
        return get_object_or_404(Order, pk=pk) if pk else None

    def get(self, request, pk=None):
        order = self._get_instance(pk)
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
        return self._render(request, form, formset)

    def post(self, request, pk=None):
        order = self._get_instance(pk)
        form = OrderForm(request.POST, request.FILES, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order or Order())

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save()
                formset.instance = order
                formset.save()
            return htmx_redirect(request, reverse("orders:list"))

        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(
            request,
            self.template_name,
            {"form": form, "formset": formset, "object": form.instance if form.instance.pk else None},
        )


class ReviewListView(LoginRequiredMixin, ListView):
    """Simple card feed of every review - no CRUD, reviews come in via Etsy
    import and are otherwise read-only here (they're already shown per-order
    in OrderDetailModalView and per-article in ArticleDetailModalView)."""

    model = Review
    template_name = "orders/review_list.html"
    context_object_name = "reviews"

    def get_queryset(self):
        qs = Review.objects.select_related("order", "order__customer").order_by("-date_reviewed")
        star_rating = self.request.GET.get("star_rating")
        if star_rating:
            qs = qs.filter(star_rating=star_rating)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_star_rating"] = self.request.GET.get("star_rating", "")
        counts = dict(Review.objects.values_list("star_rating").annotate(n=Count("id")))
        # Options carry their value as a string too, so the template can
        # compare it directly against selected_star_rating (a GET param).
        context["star_rating_options"] = [
            {"value": str(n), "stars": "★" * n + "☆" * (5 - n), "count": counts.get(n, 0)}
            for n in [5, 4, 3, 2, 1]
        ]
        context["selected_star_option"] = next(
            (o for o in context["star_rating_options"] if o["value"] == context["selected_star_rating"]), None
        )
        return context


class OrderArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    """Delete action archives instead of removing the row - see Archivable.
    Permanent deletion only happens from the Papierkorb (trash) view."""

    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        order.archive()
        return htmx_redirect(request, reverse("orders:list"))
