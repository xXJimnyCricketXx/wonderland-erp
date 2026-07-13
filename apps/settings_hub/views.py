from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from catalog.models import Article
from core.htmx_utils import htmx_redirect_fixed
from core.models import ReferenceOption
from core.reference_data import CATEGORY_GROUPS, CATEGORY_LABELS, group_slug_for_category
from finance.models import AccountMapping, SKR03Account
from knowledge.models import MaterialCategory, PackagingType
from orders.models import Order

from . import backup_utils
from .forms import AccountMappingForm, CompanyProfileForm, MaterialCategoryForm, PackagingTypeForm, SKR03AccountForm
from .models import BackupSettings, CompanyProfile
from .reset_registry import RESET_MODEL_ORDER
from .trash_registry import TRASH_REGISTRY, TRASH_REGISTRY_BY_SLUG

RESET_CONFIRM_PHRASE = "ZURÜCKSETZEN"
ORDER_RESET_CONFIRM_PHRASE = "BESTELLUNGEN LÖSCHEN"
ARTICLE_RESET_CONFIRM_PHRASE = "ARTIKEL LÖSCHEN"


class SettingsView(LoginRequiredMixin, View):
    template_name = "settings_hub/settings.html"

    def get(self, request):
        return self._render(request, CompanyProfileForm(instance=CompanyProfile.load()))

    def post(self, request):
        form = CompanyProfileForm(request.POST, instance=CompanyProfile.load())
        if form.is_valid():
            form.save()
            messages.success(request, "Stammdaten gespeichert.")
            return redirect(reverse("settings_hub:index") + "?tab=stammdaten")
        return self._render(request, form)

    def _render(self, request, form):
        existing = {}
        for opt in ReferenceOption.objects.all().order_by("category", "order", "value"):
            existing.setdefault(opt.category, []).append(opt)

        assigned = set()
        menu_groups = []
        for group in CATEGORY_GROUPS:
            categories = [
                {"slug": slug, "label": CATEGORY_LABELS.get(slug, slug), "options": existing.get(slug, [])}
                for slug in group["categories"]
            ]
            assigned.update(group["categories"])
            menu_groups.append({**group, "categories": categories})

        leftover = [
            {"slug": slug, "label": CATEGORY_LABELS.get(slug, slug), "options": options}
            for slug, options in existing.items()
            if slug not in assigned
        ]
        if leftover:
            menu_groups.append({"slug": "sonstiges", "label": "Sonstiges", "icon": "bi-three-dots", "categories": leftover})

        trash_data = []
        for entry in TRASH_REGISTRY:
            qs = entry["model"].objects.filter(
                is_archived=True, **entry["base_filter"]
            ).order_by("-archived_at")
            trash_data.append({**entry, "objects": qs})

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "reference_menu_groups": menu_groups,
                "users": User.objects.all().order_by("username"),
                "trash_data": trash_data,
                "backups": backup_utils.list_backups(),
                "backup_settings": BackupSettings.load(),
                "reset_confirm_phrase": RESET_CONFIRM_PHRASE,
                "order_reset_confirm_phrase": ORDER_RESET_CONFIRM_PHRASE,
                "article_reset_confirm_phrase": ARTICLE_RESET_CONFIRM_PHRASE,
                "packaging_types": PackagingType.objects.all().order_by("name"),
                "material_categories": MaterialCategory.objects.all().order_by("name"),
                "skr03_accounts": SKR03Account.objects.all().order_by("number"),
                "account_mappings": AccountMapping.objects.select_related("skr03_account").order_by("art", "variante"),
            },
        )


class ReferenceOptionAddView(LoginRequiredMixin, View):
    def post(self, request):
        category = request.POST.get("category", "").strip()
        value = request.POST.get("value", "").strip()
        if category and value:
            ReferenceOption.objects.get_or_create(category=category, value=value)
        modul = group_slug_for_category(category) if category else "sonstiges"
        return redirect(reverse("settings_hub:index") + f"?tab=referenzdaten&modul={modul}")


class ReferenceOptionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        option = ReferenceOption.objects.filter(pk=pk).first()
        modul = group_slug_for_category(option.category) if option else "sonstiges"
        if option:
            option.delete()
        return redirect(reverse("settings_hub:index") + f"?tab=referenzdaten&modul={modul}")


class TrashRestoreView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        entry = TRASH_REGISTRY_BY_SLUG.get(slug)
        if entry:
            obj = get_object_or_404(entry["model"], pk=pk)
            obj.unarchive()
        return redirect(reverse("settings_hub:index") + f"?tab=papierkorb&modul={slug}")


class TrashHardDeleteView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        entry = TRASH_REGISTRY_BY_SLUG.get(slug)
        if entry:
            obj = get_object_or_404(entry["model"], pk=pk)
            obj.delete()
        return redirect(reverse("settings_hub:index") + f"?tab=papierkorb&modul={slug}")


class TrashEmptyView(LoginRequiredMixin, View):
    def post(self, request, slug):
        entry = TRASH_REGISTRY_BY_SLUG.get(slug)
        if entry:
            entry["model"].objects.filter(is_archived=True, **entry["base_filter"]).delete()
        return redirect(reverse("settings_hub:index") + f"?tab=papierkorb&modul={slug}")


class BackupCreateView(LoginRequiredMixin, View):
    def post(self, request):
        backup_utils.create_backup()
        backup_utils.enforce_retention(BackupSettings.load().keep_count)
        messages.success(request, "Backup erstellt.")
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class BackupSettingsUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        raw = request.POST.get("keep_count", "3")
        obj = BackupSettings.load()
        obj.keep_count = int(raw) if raw.isdigit() and int(raw) > 0 else obj.keep_count
        obj.save()
        backup_utils.enforce_retention(obj.keep_count)
        messages.success(request, "Backup-Einstellungen gespeichert.")
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class BackupDownloadView(LoginRequiredMixin, View):
    def get(self, request, filename):
        path = backup_utils.get_backup_path(filename)
        if path is None:
            raise Http404
        return FileResponse(open(path, "rb"), as_attachment=True, filename=filename)


class BackupDeleteView(LoginRequiredMixin, View):
    def post(self, request, filename):
        path = backup_utils.get_backup_path(filename)
        if path is not None:
            path.unlink()
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class DatabaseResetView(UserPassesTestMixin, View):
    """Danger Zone: wipes all business data, keeps auth (Users/Groups) and
    backup settings intact, and always creates a safety-net backup first."""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Nur Administratoren können die Datenbank zurücksetzen.")
        return redirect(reverse("settings_hub:index") + "?tab=backups")

    def post(self, request):
        if request.POST.get("confirm_text", "") != RESET_CONFIRM_PHRASE:
            messages.error(request, "Bestätigungstext stimmte nicht überein - nichts wurde gelöscht.")
            return redirect(reverse("settings_hub:index") + "?tab=backups")

        backup_utils.create_backup()

        for model in RESET_MODEL_ORDER:
            model.objects.all().delete()

        messages.success(
            request,
            "Datenbank wurde zurückgesetzt (Benutzerkonten blieben erhalten). "
            "Ein Sicherungs-Backup wurde direkt davor automatisch erstellt.",
        )
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class OrderResetView(UserPassesTestMixin, View):
    """Danger Zone: deletes only Bestellungen (+ their Positionen/Bewertungen
    via CASCADE), keeps everything else intact. Safety-net backup first."""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Nur Administratoren können Bestellungen zurücksetzen.")
        return redirect(reverse("settings_hub:index") + "?tab=backups")

    def post(self, request):
        if request.POST.get("confirm_text", "") != ORDER_RESET_CONFIRM_PHRASE:
            messages.error(request, "Bestätigungstext stimmte nicht überein - nichts wurde gelöscht.")
            return redirect(reverse("settings_hub:index") + "?tab=backups")

        backup_utils.create_backup()

        Order.objects.all().delete()

        messages.success(
            request,
            "Alle Bestellungen wurden gelöscht. "
            "Ein Sicherungs-Backup wurde direkt davor automatisch erstellt.",
        )
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class ArticleResetView(UserPassesTestMixin, View):
    """Danger Zone: deletes only Artikel (+ Varianten via CASCADE), keeps
    everything else intact. Safety-net backup first."""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Nur Administratoren können Artikel zurücksetzen.")
        return redirect(reverse("settings_hub:index") + "?tab=backups")

    def post(self, request):
        if request.POST.get("confirm_text", "") != ARTICLE_RESET_CONFIRM_PHRASE:
            messages.error(request, "Bestätigungstext stimmte nicht überein - nichts wurde gelöscht.")
            return redirect(reverse("settings_hub:index") + "?tab=backups")

        backup_utils.create_backup()

        Article.objects.all().delete()

        messages.success(
            request,
            "Alle Artikel wurden gelöscht. "
            "Ein Sicherungs-Backup wurde direkt davor automatisch erstellt.",
        )
        return redirect(reverse("settings_hub:index") + "?tab=backups")


class PackagingTypeModalMixin(LoginRequiredMixin):
    model = PackagingType
    form_class = PackagingTypeForm
    template_name = "settings_hub/_packaging_type_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=infothek")


class PackagingTypeCreateView(PackagingTypeModalMixin, CreateView):
    pass


class PackagingTypeUpdateView(PackagingTypeModalMixin, UpdateView):
    pass


class PackagingTypeDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = PackagingType

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=infothek")


class MaterialCategoryModalMixin(LoginRequiredMixin):
    model = MaterialCategory
    form_class = MaterialCategoryForm
    template_name = "settings_hub/_material_category_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=infothek")


class MaterialCategoryCreateView(MaterialCategoryModalMixin, CreateView):
    pass


class MaterialCategoryUpdateView(MaterialCategoryModalMixin, UpdateView):
    pass


class MaterialCategoryDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = MaterialCategory

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=infothek")


class SKR03AccountCreateView(LoginRequiredMixin, View):
    """Plain inline-add (same pattern as ReferenceOptionAddView) - no modal,
    matches the "neuer Wert + Hinzufügen" row every other Referenzdaten
    category uses."""

    def post(self, request):
        number = request.POST.get("number", "").strip()
        name = request.POST.get("name", "").strip()
        if number and name:
            SKR03Account.objects.get_or_create(number=number, defaults={"name": name})
        return redirect(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")


class SKR03AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = SKR03Account
    form_class = SKR03AccountForm
    template_name = "settings_hub/_skr03_account_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")


class SKR03AccountDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = SKR03Account

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")


class AccountMappingCreateView(LoginRequiredMixin, View):
    """Plain inline-add (same pattern as ReferenceOptionAddView) - no modal."""

    def post(self, request):
        art = request.POST.get("art", "").strip()
        variante = request.POST.get("variante", "").strip()
        skr03_account_id = request.POST.get("skr03_account", "").strip()
        if art and skr03_account_id:
            AccountMapping.objects.get_or_create(
                art=art, variante=variante, defaults={"skr03_account_id": skr03_account_id}
            )
        return redirect(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")


class AccountMappingUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountMapping
    form_class = AccountMappingForm
    template_name = "settings_hub/_account_mapping_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")


class AccountMappingDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = AccountMapping

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect_fixed(reverse("settings_hub:index") + "?tab=referenzdaten&modul=finanzen")
