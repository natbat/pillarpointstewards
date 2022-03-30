import datetime
import pytest
from django.utils.timezone import make_aware
import pytz


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


@pytest.fixture
def admin_user_has_shift(admin_user):
    dt = make_aware(
        datetime.datetime.utcnow() + datetime.timedelta(hours=96),
        timezone=pytz.timezone("America/Los_Angeles"),
    )
    admin_user.shifts.create(
        shift_start=dt,
        shift_end=dt + datetime.timedelta(hours=2),
        dawn=dt - datetime.timedelta(hours=1),
        dusk=dt - +datetime.timedelta(hours=5),
    )
