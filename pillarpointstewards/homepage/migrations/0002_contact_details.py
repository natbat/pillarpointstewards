from django.db import migrations


def insert_contact_details(apps, schema_editor):
    Fragment = apps.get_model("homepage", "Fragment")
    Fragment.objects.get_or_create(
        slug="contact_details", fragment="Contact details go here"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            insert_contact_details, reverse_code=lambda apps, schema_editor: None
        )
    ]
