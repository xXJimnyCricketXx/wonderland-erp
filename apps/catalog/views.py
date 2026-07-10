from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

from contacts.models import Supplier
from core.models import ReferenceOption

from .forms import ArticleForm
from .models import Article


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "catalog/article_list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        # Variants show up on their parent's detail page, not as their own
        # row in the main table. Archived articles are hidden by default -
        # "archive, don't delete" - rather than gone from the list entirely.
        qs = Article.objects.filter(
            parent_article__isnull=True, is_archived=False
        ).select_related("supplier")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(sku__icontains=query))

        is_active = self.request.GET.get("is_active")
        if is_active in ("1", "0"):
            qs = qs.filter(is_active=bool(int(is_active)))

        supplier_id = self.request.GET.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        return qs.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.filter(is_archived=False).order_by("full_name")
        context["categories"] = ReferenceOption.objects.filter(
            category="article_category"
        ).order_by("order", "value")
        context["query"] = self.request.GET.get("q", "")
        context["selected_is_active"] = self.request.GET.get("is_active", "")
        context["selected_supplier"] = self.request.GET.get("supplier", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["trash_count"] = Article.objects.filter(
            is_archived=True, parent_article__isnull=True
        ).count()
        return context


class ArticleDetailModalView(LoginRequiredMixin, DetailView):
    """Read-only 'product page' shown by the eye icon - a real detail view,
    not the edit form. Its footer links into ArticleUpdateView for editing."""

    model = Article
    template_name = "catalog/_article_detail_modal.html"
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Reviews only attach to Order, not Article, and Etsy gives no way
        # to tell which review-row within a multi-item order belongs to which
        # item - so only single-item orders can be attributed unambiguously.
        from orders.models import Review

        single_item_order_ids = [
            item.order_id
            for item in self.object.order_items.select_related("order").all()
            if item.order.items.count() == 1
        ]
        context["reviews"] = Review.objects.filter(
            order_id__in=single_item_order_ids
        ).order_by("-date_reviewed")
        return context


class ArticleModalMixin(LoginRequiredMixin):
    """Shared by create/update: both render into the same modal partial and,
    on success, tell HTMX to do a full-page redirect back to the list rather
    than trying to patch the table in place."""

    model = Article
    form_class = ArticleForm
    template_name = "catalog/_article_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("catalog:list")
        return response


class ArticleCreateView(ArticleModalMixin, CreateView):
    pass


class ArticleUpdateView(ArticleModalMixin, UpdateView):
    pass


class ArticleArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    """Delete action archives instead of removing the row - see Archivable.
    Permanent deletion only happens from the Papierkorb (trash) view."""

    model = Article

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        article.archive()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("catalog:list")
        return response
