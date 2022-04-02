import re
import unicodedata
from django.shortcuts import render
from functools import wraps

_disallowed_characters = re.compile(r"[^a-zA-Z0-9-]")
_duplicate_hyphens = re.compile(r"-+")


def suggest_username(name):
    """
    Returns name with éîü -> eiu and with non-alphanumeric
    characters converted to "-" and multiple "--" collapsed
    to one and any leading or trailing "-" removed
    """
    nfkd = unicodedata.normalize("NFKD", name)
    s = nfkd.encode("ascii", "ignore").decode("utf-8")
    # Remove non-alphanumeric characters
    s = _disallowed_characters.sub("-", s)
    # Remove duplicate "-"
    s = _duplicate_hyphens.sub("-", s)
    # Strip trailing/leading hyphens
    s = s.strip("-")
    # Make sure we don't return an empty string
    return s or "blank"


def active_user_required(view_fn):
    @wraps(view_fn)
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_active:
            render(request, "inactive.html")
        else:
            return view_fn(request, *args, **kwargs)

    return inner
