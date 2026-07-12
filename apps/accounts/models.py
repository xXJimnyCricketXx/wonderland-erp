from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Extends the built-in User with fields it doesn't have (currently just
    the avatar) - kept as a separate one-to-one row rather than a custom User
    model, since swapping AUTH_USER_MODEL mid-project is a much bigger,
    harder-to-reverse change than this project needs for one extra field."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField("Profilbild", upload_to="avatars/", blank=True, null=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profile"

    def __str__(self):
        return f"Profil von {self.user.username}"
