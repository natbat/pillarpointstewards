from django.db import models
from django.contrib.auth.models import User
from shifts.models import Photo


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_photo = models.ForeignKey(
        Photo, on_delete=models.SET_NULL, null=True, blank=True
    )

    def thumbnail_url(self):
        return (
            f'https://s3.amazonaws.com/images.tidepoolstewards.com/{self.profile_photo.thumbnail_path}'
            if (self.profile_photo and self.profile_photo.thumbnail_path)
            else None
        )

    def name(self):
        return self.display_name or self.user.username

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return "/profiles/{}".format(self.user.username)

    @classmethod
    def for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]
