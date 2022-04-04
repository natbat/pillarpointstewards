from pytest_django.asserts import assertHTMLEqual
from django.utils import timezone
from .models import TidePrediction
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


def test_tide_svg_on_date_with_shift(tide_predictions, client):
    shift = Shift.objects.create(
        dawn=datetime.datetime(2022, 4, 21, 6, tzinfo=timezone.utc),
        dusk=datetime.datetime(2022, 4, 21, 20, tzinfo=timezone.utc),
        shift_start=datetime.datetime(2022, 4, 21, 8, 30, tzinfo=timezone.utc),
        shift_end=datetime.datetime(2022, 4, 21, 10, 30, tzinfo=timezone.utc),
        mllw_feet=-1.055,
        lowest_tide=datetime.datetime(2022, 4, 21, 9, 30, tzinfo=timezone.utc),
    )
    response = client.get("/debug/tide-times-just-svg/2022-04-21/")
    html = response.content.decode("utf-8")
    assertHTMLEqual(
        html,
        textwrap.dedent(
            """
        <div class="day-alone">
          <div class="shift-view">
            <div class="day-view" style="
              background: linear-gradient(90deg,
              #176AB8 0%,
              #97bcdf 24.95%,
              #d1e1f1 26.88%,
              #FFFFFF 54.78%,
              #d1e1f1 82.69%,
              #97bcdf 84.63%,
              #176AB8 100%
              );
            ">
              <div class="shift-window" style="left:35.42%; width: 8.329999999999998%;">
                <span class="start-time">8:30am</span>
                <span class="end-time">10:30am</span>
              </div>
              <svg style="width: 100%; height: 60px; opacity: 0.5" viewBox="0 -2 240 104" preserveAspectRatio="none">
                <polyline fill="none" stroke="#176AB8" stroke-width="2" points="0,6.04 1,5.11 2,4.27 3,3.49 4,2.79 5,2.15 6,1.58 7,1.10 8,0.72 9,0.40 10,0.18 11,0.04 12,0.00 13,0.04 14,0.18 15,0.42 16,0.74 17,1.16 18,1.68 19,2.31 20,3.03 21,3.83 22,4.73 23,5.74 24,6.82 25,7.98 26,9.25 27,10.57 28,11.99 29,13.48 30,15.04 31,16.67 32,18.37 33,20.12 34,21.94 35,23.81 36,25.71 37,27.68 38,29.68 39,31.71 40,33.79 41,35.90 42,38.03 43,40.17 44,42.34 45,44.52 46,46.73 47,48.92 48,51.12 49,53.33 50,55.54 51,57.72 52,59.89 53,62.05 54,64.18 55,66.29 56,68.37 57,70.42 58,72.40 59,74.37 60,76.27 61,78.12 62,79.92 63,81.67 64,83.33 65,84.94 66,86.48 67,87.95 68,89.33 69,90.65 70,91.88 71,93.02 72,94.10 73,95.07 74,95.97 75,96.77 76,97.49 77,98.11 78,98.66 79,99.12 80,99.46 81,99.74 82,99.90 83,100.00 84,99.98 85,99.90 86,99.70 87,99.44 88,99.08 89,98.64 90,98.09 91,97.49 92,96.79 93,96.01 94,95.17 95,94.24 96,93.24 97,92.18 98,91.05 99,89.85 100,88.61 101,87.30 102,85.94 103,84.54 104,83.09 105,81.61 106,80.08 107,78.52 108,76.96 109,75.35 110,73.73 111,72.08 112,70.44 113,68.77 114,67.11 115,65.44 116,63.78 117,62.11 118,60.47 119,58.84 120,57.22 121,55.62 122,54.03 123,52.47 124,50.94 125,49.44 126,47.97 127,46.55 128,45.17 129,43.82 130,42.54 131,41.28 132,40.09 133,38.95 134,37.87 135,36.86 136,35.90 137,35.00 138,34.18 139,33.41 140,32.73 141,32.11 142,31.55 143,31.07 144,30.67 145,30.32 146,30.04 147,29.84 148,29.70 149,29.62 150,29.60 151,29.64 152,29.76 153,29.90 154,30.12 155,30.37 156,30.69 157,31.03 158,31.43 159,31.85 160,32.31 161,32.81 162,33.35 163,33.91 164,34.50 165,35.12 166,35.74 167,36.40 168,37.06 169,37.77 170,38.47 171,39.17 172,39.89 173,40.61 174,41.36 175,42.08 176,42.80 177,43.52 178,44.22 179,44.91 180,45.59 181,46.25 182,46.89 183,47.49 184,48.07 185,48.62 186,49.12 187,49.60 188,50.02 189,50.42 190,50.74 191,51.04 192,51.28 193,51.48 194,51.62 195,51.70 196,51.74 197,51.70 198,51.62 199,51.50 200,51.30 201,51.06 202,50.76 203,50.42 204,50.02 205,49.56 206,49.06 207,48.50 208,47.87 209,47.23 210,46.51 211,45.77 212,44.97 213,44.12 214,43.26 215,42.34 216,41.38 217,40.37 218,39.35 219,38.29 220,37.20 221,36.08 222,34.94 223,33.79 224,32.61 225,31.41 226,30.20 227,28.98 228,27.76 229,26.53 230,25.31 231,24.11 232,22.88 233,21.70 234,20.50 235,19.33 236,18.19 237,17.07"></polyline>
              </svg>
              <span class="minima" style="left: 39.58%">
                <span class="time">9:30am</span>
              </span>
            </div>
          </div>
        </div>
        """
        ),
    )


def test_tide_svg_on_date_without_shift(tide_predictions, client):
    response = client.get("/debug/tide-times-just-svg/2022-04-21/")
    html = response.content.decode("utf-8")
    assertHTMLEqual(
        html,
        textwrap.dedent(
            """
        <div class="day-alone">
          <div class="shift-view">
            <div class="day-view" style="
              background: linear-gradient(90deg,
              #176AB8 0%,
              #97bcdf 24.95%,
              #d1e1f1 26.88%,
              #FFFFFF 54.78%,
              #d1e1f1 82.69%,
              #97bcdf 84.63%,
              #176AB8 100%
              );
            ">
              <svg style="width: 100%; height: 60px; opacity: 0.5" viewBox="0 -2 240 104" preserveAspectRatio="none">
                <polyline fill="none" stroke="#176AB8" stroke-width="2" points="0,6.04 1,5.11 2,4.27 3,3.49 4,2.79 5,2.15 6,1.58 7,1.10 8,0.72 9,0.40 10,0.18 11,0.04 12,0.00 13,0.04 14,0.18 15,0.42 16,0.74 17,1.16 18,1.68 19,2.31 20,3.03 21,3.83 22,4.73 23,5.74 24,6.82 25,7.98 26,9.25 27,10.57 28,11.99 29,13.48 30,15.04 31,16.67 32,18.37 33,20.12 34,21.94 35,23.81 36,25.71 37,27.68 38,29.68 39,31.71 40,33.79 41,35.90 42,38.03 43,40.17 44,42.34 45,44.52 46,46.73 47,48.92 48,51.12 49,53.33 50,55.54 51,57.72 52,59.89 53,62.05 54,64.18 55,66.29 56,68.37 57,70.42 58,72.40 59,74.37 60,76.27 61,78.12 62,79.92 63,81.67 64,83.33 65,84.94 66,86.48 67,87.95 68,89.33 69,90.65 70,91.88 71,93.02 72,94.10 73,95.07 74,95.97 75,96.77 76,97.49 77,98.11 78,98.66 79,99.12 80,99.46 81,99.74 82,99.90 83,100.00 84,99.98 85,99.90 86,99.70 87,99.44 88,99.08 89,98.64 90,98.09 91,97.49 92,96.79 93,96.01 94,95.17 95,94.24 96,93.24 97,92.18 98,91.05 99,89.85 100,88.61 101,87.30 102,85.94 103,84.54 104,83.09 105,81.61 106,80.08 107,78.52 108,76.96 109,75.35 110,73.73 111,72.08 112,70.44 113,68.77 114,67.11 115,65.44 116,63.78 117,62.11 118,60.47 119,58.84 120,57.22 121,55.62 122,54.03 123,52.47 124,50.94 125,49.44 126,47.97 127,46.55 128,45.17 129,43.82 130,42.54 131,41.28 132,40.09 133,38.95 134,37.87 135,36.86 136,35.90 137,35.00 138,34.18 139,33.41 140,32.73 141,32.11 142,31.55 143,31.07 144,30.67 145,30.32 146,30.04 147,29.84 148,29.70 149,29.62 150,29.60 151,29.64 152,29.76 153,29.90 154,30.12 155,30.37 156,30.69 157,31.03 158,31.43 159,31.85 160,32.31 161,32.81 162,33.35 163,33.91 164,34.50 165,35.12 166,35.74 167,36.40 168,37.06 169,37.77 170,38.47 171,39.17 172,39.89 173,40.61 174,41.36 175,42.08 176,42.80 177,43.52 178,44.22 179,44.91 180,45.59 181,46.25 182,46.89 183,47.49 184,48.07 185,48.62 186,49.12 187,49.60 188,50.02 189,50.42 190,50.74 191,51.04 192,51.28 193,51.48 194,51.62 195,51.70 196,51.74 197,51.70 198,51.62 199,51.50 200,51.30 201,51.06 202,50.76 203,50.42 204,50.02 205,49.56 206,49.06 207,48.50 208,47.87 209,47.23 210,46.51 211,45.77 212,44.97 213,44.12 214,43.26 215,42.34 216,41.38 217,40.37 218,39.35 219,38.29 220,37.20 221,36.08 222,34.94 223,33.79 224,32.61 225,31.41 226,30.20 227,28.98 228,27.76 229,26.53 230,25.31 231,24.11 232,22.88 233,21.70 234,20.50 235,19.33 236,18.19 237,17.07"></polyline>
              </svg>
            </div>
          </div>
        </div>
        """
        ),
    )


def test_tide_svg_on_date_with_no_stored_tide_data(client, db):
    response = client.get("/debug/tide-times-just-svg/2022-03-01/")
    assert response.content.strip() == b""


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
