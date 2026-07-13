from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import View

from .models import Message

User = get_user_model()


def _contacts_context(me):
    """Every other active user, with last message + unread count, most
    recently-active conversation first."""
    contacts = []
    for other in User.objects.filter(is_active=True).exclude(pk=me.pk).order_by("username"):
        last = Message.objects.filter(
            Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
        ).order_by("-created_at").first()
        unread = Message.objects.filter(sender=other, recipient=me, read_at__isnull=True).count()
        contacts.append({"user": other, "last_message": last, "unread": unread})
    contacts.sort(key=lambda c: (c["last_message"] is not None, c["last_message"].created_at if c["last_message"] else None), reverse=True)
    return contacts


def _mark_read_and_get_messages(me, other):
    Message.objects.filter(sender=other, recipient=me, read_at__isnull=True).update(read_at=timezone.now())
    return Message.objects.filter(
        Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
    ).order_by("created_at")


class MessagesView(LoginRequiredMixin, View):
    """Same URL/view for a direct page load and an htmx contact-list click -
    branches on request.htmx (django-htmx) to return either the full page
    or just the conversation partial, so hx-push-url keeps the address bar
    accurate without needing a second URL."""

    def get(self, request, user_id=None):
        active_user = get_object_or_404(User, pk=user_id) if user_id else None
        context = {"contacts": _contacts_context(request.user), "active_user": active_user}
        if active_user:
            context["conversation_messages"] = _mark_read_and_get_messages(request.user, active_user)
        if request.htmx and active_user:
            return render(request, "messaging/_conversation_full.html", context)
        return render(request, "messaging/index.html", context)


class MessageListView(LoginRequiredMixin, View):
    """Just the message bubbles - polling target only. Deliberately never
    includes the send <form>, so the periodic refresh can't wipe out
    whatever the user is currently typing (it did, before this was split
    out from the conversation-content view - a real reported bug)."""

    def get(self, request, user_id):
        active_user = get_object_or_404(User, pk=user_id)
        messages_qs = _mark_read_and_get_messages(request.user, active_user)
        return render(request, "messaging/_message_list.html", {
            "active_user": active_user,
            "conversation_messages": messages_qs,
        })


class MessageSendView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        recipient = get_object_or_404(User, pk=user_id)
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(sender=request.user, recipient=recipient, body=body)
        messages_qs = _mark_read_and_get_messages(request.user, recipient)
        return render(request, "messaging/_message_list.html", {
            "active_user": recipient,
            "conversation_messages": messages_qs,
        })


class ContactListView(LoginRequiredMixin, View):
    def get(self, request):
        active_id = request.GET.get("active")
        return render(request, "messaging/_contact_list.html", {
            "contacts": _contacts_context(request.user),
            "active_user_id": int(active_id) if active_id else None,
        })


class UnreadBadgeView(LoginRequiredMixin, View):
    def get(self, request):
        count = Message.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return render(request, "messaging/_badge.html", {"unread_message_count": count})
