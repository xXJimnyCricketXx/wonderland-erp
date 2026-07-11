from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

from core.sorting import resolve_sort

from .forms import OrderForm
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
        base_qs = Order.objects.filter(is_archived=False)
        context["statuses"] = (
            base_qs.exclude(status="").order_by("status").values_list("status", flat=True).distinct()
        )
        context["order_types"] = (
            base_qs.exclude(order_type="").order_by("order_type").values_list("order_type", flat=True).distinct()
        )
        context["query"] = self.request.GET.get("q", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_order_type"] = self.request.GET.get("order_type", "")
        context["trash_count"] = Order.objects.filter(is_archived=True).count()
        return context


class OrderDetailModalView(LoginRequiredMixin, DetailView):
    """Read-only 'Bestellschein' shown by the eye icon - its footer links
    into OrderUpdateView for editing."""

    model = Order
    template_name = "orders/_order_detail_modal.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_items"] = self.object.items.select_related("article").all()
        context["reviews"] = self.object.reviews.all()
        return context


class OrderModalMixin(LoginRequiredMixin):
    model = Order
    form_class = OrderForm
    template_name = "orders/_order_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("orders:list")
        return response


class OrderCreateView(OrderModalMixin, CreateView):
    pass


class OrderUpdateView(OrderModalMixin, UpdateView):
    pass


class ReviewListView(LoginRequiredMixin, ListView):
    """Simple card feed of every review - no CRUD, reviews come in via Etsy
    import and are otherwise read-only here (they're already shown per-order
    in OrderDetailModalView and per-article in ArticleDetailModalView)."""

    model = Review
    template_name = "orders/review_list.html"
    context_object_name = "reviews"

    def get_queryset(self):
        return Review.objects.select_related("order", "order__customer").order_by("-date_reviewed")


class OrderArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    """Delete action archives instead of removing the row - see Archivable.
    Permanent deletion only happens from the Papierkorb (trash) view."""

    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        order.archive()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("orders:list")
        return response
