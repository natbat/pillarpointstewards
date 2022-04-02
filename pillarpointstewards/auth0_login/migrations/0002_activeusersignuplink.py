# Generated by Django 4.0.3 on 2022-04-02 21:08

import auth0_login.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth0_login", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActiveUserSignupLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "secret",
                    models.CharField(
                        default=auth0_login.models.random_token, max_length=32
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="If not active the link will no longer create activated accounts",
                    ),
                ),
                (
                    "created_users",
                    models.ManyToManyField(
                        blank=True, related_name="+", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
    ]
