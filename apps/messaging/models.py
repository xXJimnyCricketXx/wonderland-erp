from django.conf import settings
from django.db import models


class Message(models.Model):
    """Direct 1:1 chat message between two registered users - no group
    chats. `read_at` gets set the moment the recipient opens/polls the
    conversation (see messaging/views.py), driving both the per-contact
    unread badge and the navbar bell-style badge."""

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Absender",
        on_delete=models.CASCADE, related_name="sent_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Empfänger",
        on_delete=models.CASCADE, related_name="received_messages",
    )
    body = models.TextField("Nachricht")
    created_at = models.DateTimeField("Gesendet am", auto_now_add=True)
    read_at = models.DateTimeField("Gelesen am", blank=True, null=True)

    class Meta:
        verbose_name = "Nachricht"
        verbose_name_plural = "Nachrichten"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.body[:30]}"
