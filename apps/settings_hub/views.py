from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import View

from core.models import ReferenceOption
from core.reference_data import CATEGORY_LABELS

from . import backup_utils
from .forms import CompanyProfileForm
from .models import BackupSettings, CompanyProfile
from .reset_registry import RESET_MODEL_ORDER
from .trash_registry import TRASH_REGISTRY, TRASH_REGISTRY_BY_SLUG

RESET_CONFIRM_PHRASE = "ZURÜCKSETZEN"


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

        groups = []
        for slug, label in CATEGORY_LABELS.items():
            groups.append({"slug": slug, "label": label, "options": existing.get(slug, [])})
        for slug, options in existing.items():
            if slug not in CATEGORY_LABELS:
                groups.append({"slug": slug, "label": slug, "options": options})

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
                "reference_groups": groups,
                "users": User.objects.all().order_by("username"),
                "trash_data": trash_data,
                "backups": backup_utils.list_backups(),
                "backup_settings": BackupSettings.load(),
                "reset_confirm_phrase": RESET_CONFIRM_PHRASE,
            },
        )


class ReferenceOptionAddView(LoginRequiredMixin, View):
    def post(self, request):
        category = request.POST.get("category", "").strip()
        value = request.POST.get("value", "").strip()
        if category and value:
            ReferenceOption.objects.get_or_create(category=category, value=value)
        return redirect(reverse("settings_hub:index") + "?tab=referenzdaten")


class ReferenceOptionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ReferenceOption.objects.filter(pk=pk).delete()
        return redirect(reverse("settings_hub:index") + "?tab=referenzdaten")


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
