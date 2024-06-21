from pytest_django.asserts import assertHTMLEqual
from datetime import timezone
from .models import TidePrediction, Location, SunriseSunset
from shifts.models import Shift
import datetime
import pytest
import textwrap

# Workaround 'Diff is x characters long. Set self.maxDiff to None to see it.'
from unittest import TestCase

TestCase.maxDiff = None


@pytest.fixture
def tide_predictions(db):
    start = datetime.datetime(2022, 4, 21, 0, 0, 0, tzinfo=timezone.utc)
    to_insert = []
    for i, height in enumerate(HEIGHTS):
        to_insert.append(
            TidePrediction(
                station_id=9414131,
                dt=start + datetime.timedelta(minutes=i * 6),
                mllw_feet=height,
            )
        )
    TidePrediction.objects.bulk_create(to_insert)


def test_tide_predictions_fixture(tide_predictions):
    assert TidePrediction.objects.count() == 240
    first = TidePrediction.objects.order_by("dt").first()
    last = TidePrediction.objects.order_by("-dt").first()
    assert first.dt.time().isoformat() == "00:00:00"
    assert last.dt.time().isoformat() == "23:54:00"


# These are each 6 minutes apart, from 00:00 to 23:54
HEIGHTS = [
    4.84,
    4.889,
    4.935,
    4.977,
    5.016,
    5.051,
    5.083,
    5.111,
    5.135,
    5.154,
    5.17,
    5.181,
    5.188,
    5.19,
    5.188,
    5.181,
    5.169,
    5.153,
    5.132,
    5.106,
    5.075,
    5.039,
    4.999,
    4.954,
    4.904,
    4.85,
    4.792,
    4.729,
    4.663,
    4.592,
    4.518,
    4.44,
    4.359,
    4.274,
    4.187,
    4.096,
    4.003,
    3.908,
    3.81,
    3.71,
    3.609,
    3.505,
    3.4,
    3.294,
    3.187,
    3.079,
    2.97,
    2.86,
    2.751,
    2.641,
    2.531,
    2.421,
    2.312,
    2.204,
    2.096,
    1.99,
    1.885,
    1.781,
    1.679,
    1.58,
    1.482,
    1.387,
    1.295,
    1.205,
    1.118,
    1.035,
    0.955,
    0.878,
    0.805,
    0.736,
    0.67,
    0.609,
    0.552,
    0.498,
    0.45,
    0.405,
    0.365,
    0.329,
    0.298,
    0.271,
    0.248,
    0.231,
    0.217,
    0.209,
    0.204,
    0.205,
    0.209,
    0.219,
    0.232,
    0.25,
    0.272,
    0.299,
    0.329,
    0.364,
    0.403,
    0.445,
    0.491,
    0.541,
    0.594,
    0.65,
    0.71,
    0.772,
    0.837,
    0.905,
    0.975,
    1.047,
    1.121,
    1.197,
    1.275,
    1.353,
    1.433,
    1.514,
    1.596,
    1.678,
    1.761,
    1.844,
    1.927,
    2.01,
    2.093,
    2.175,
    2.256,
    2.337,
    2.417,
    2.496,
    2.574,
    2.65,
    2.725,
    2.798,
    2.869,
    2.938,
    3.005,
    3.069,
    3.132,
    3.191,
    3.248,
    3.302,
    3.352,
    3.4,
    3.445,
    3.486,
    3.524,
    3.558,
    3.589,
    3.617,
    3.641,
    3.661,
    3.678,
    3.692,
    3.702,
    3.709,
    3.713,
    3.714,
    3.712,
    3.706,
    3.699,
    3.688,
    3.676,
    3.66,
    3.643,
    3.623,
    3.602,
    3.579,
    3.554,
    3.527,
    3.499,
    3.47,
    3.439,
    3.408,
    3.375,
    3.342,
    3.307,
    3.272,
    3.237,
    3.201,
    3.165,
    3.128,
    3.092,
    3.056,
    3.02,
    2.985,
    2.951,
    2.917,
    2.884,
    2.852,
    2.822,
    2.793,
    2.766,
    2.741,
    2.717,
    2.696,
    2.676,
    2.66,
    2.645,
    2.633,
    2.623,
    2.616,
    2.612,
    2.61,
    2.612,
    2.616,
    2.622,
    2.632,
    2.644,
    2.659,
    2.676,
    2.696,
    2.719,
    2.744,
    2.772,
    2.803,
    2.835,
    2.871,
    2.908,
    2.948,
    2.99,
    3.033,
    3.079,
    3.127,
    3.177,
    3.228,
    3.281,
    3.335,
    3.391,
    3.448,
    3.505,
    3.564,
    3.624,
    3.684,
    3.745,
    3.806,
    3.867,
    3.928,
    3.988,
    4.049,
    4.108,
    4.168,
    4.226,
    4.283,
    4.339,
    4.393,
]


@pytest.mark.django_db
def test_location_populate_sunrise_sunsets():
    # Should have one location from fixtures
    location = Location.objects.get(name="Pillar Point")
    assert location.sunrise_sunsets.count() == 0
    location.populate_sunrise_sunsets()
    assert location.sunrise_sunsets.count() == 365

@pytest.mark.django_db
def test_should_populate_tide_predictions():
    # Create a location and associated tide predictions
    location = Location.objects.create(
        name="Test Location",
        station_id=9414131,
        latitude=37.49542392,
        longitude=-122.49865193,
        time_zone="America/Los_Angeles",
    )
    # Create tide predictions for the past 6 months
    past_date = datetime.datetime.now() - datetime.timedelta(days=180)
    TidePrediction.objects.create(
        station_id=location.station_id,
        dt=past_date,
        mllw_feet=5.0,
    )
    # Verify that should_populate_tide_predictions returns True
    assert TidePrediction.should_populate_tide_predictions(location.station_id) is True
    # Create a tide prediction for less than 6 months away
    future_date = datetime.datetime.now() + datetime.timedelta(days=179)
    TidePrediction.objects.create(
        station_id=location.station_id,
        dt=future_date,
        mllw_feet=5.0,
    )
    # Verify that should_populate_tide_predictions now returns False
    assert TidePrediction.should_populate_tide_predictions(location.station_id) is False
