from .models import Message


def unread_messages(request):
    if not request.user.is_authenticated:
        return {}
    count = Message.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return {"unread_message_count": count}
