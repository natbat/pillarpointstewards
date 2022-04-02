import re
import unicodedata

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
