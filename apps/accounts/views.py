from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View

from .forms import AvatarForm, ProfileForm, StyledPasswordChangeForm
from .models import Profile


class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return self._render(
            request, ProfileForm(instance=request.user),
            StyledPasswordChangeForm(request.user), AvatarForm(instance=profile),
        )

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil gespeichert.")
            return redirect(reverse("accounts:profile"))
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return self._render(request, form, StyledPasswordChangeForm(request.user), AvatarForm(instance=profile))

    def _render(self, request, form, password_form, avatar_form):
        return render(request, self.template_name, {
            "form": form, "password_form": password_form, "avatar_form": avatar_form,
        })


class ProfilePasswordChangeView(LoginRequiredMixin, View):
    def post(self, request):
        password_form = StyledPasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Passwort geändert.")
            return redirect(reverse("accounts:profile"))

        messages.error(request, "Passwort konnte nicht geändert werden - bitte Eingaben prüfen.")
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return render(request, "accounts/profile.html", {
            "form": ProfileForm(instance=request.user),
            "password_form": password_form,
            "avatar_form": AvatarForm(instance=profile),
        })


class ProfileAvatarView(LoginRequiredMixin, View):
    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = AvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profilbild gespeichert.")
        else:
            messages.error(request, "Profilbild konnte nicht gespeichert werden.")
        return redirect(reverse("accounts:profile"))
