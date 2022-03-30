from django.db import models


class Fragment(models.Model):
    slug = models.SlugField(primary_key=True)
    fragment = models.TextField()

    def __str__(self):
        return self.slug
