# Generated by Django 4.2.6 on 2023-10-18 14:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("auth0_login", "0003_activeusersignuplink_comment"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ActiveUserSignupLink",
        ),
    ]
