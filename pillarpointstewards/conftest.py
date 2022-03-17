import pytest


@pytest.fixture(autouse=True)
def configure_whitenoise(settings):
    """
    Get rid of whitenoise "No directory at" warning, as it's not helpful when running tests.
    https://github.com/evansd/whitenoise/issues/215#issuecomment-558621213
    """
    settings.WHITENOISE_AUTOREFRESH = True

    # To avoid ValueError: Missing staticfiles manifest entry
    # https://github.com/natbat/pillarpointstewards/issues/16#issuecomment-1071440848
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
