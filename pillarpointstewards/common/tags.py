from django import template
from django.utils.safestring import mark_safe
import json

entity_translation_table = str.maketrans({char: f"&#{ord(char)};" for char in "<>&'\""})

register = template.Library()


@register.filter(name="to_json")
def to_json(value):
    return mark_safe(
        json.dumps(value, default=repr).translate(entity_translation_table)
    )
