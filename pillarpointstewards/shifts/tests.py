from shifts.models import Shift
import json
import pytest


def test_import_shifts(admin_client):
    assert Shift.objects.count() == 0
    response = admin_client.post(
        "/admin/import-shifts/",
        {
            "data": json.dumps(
                [
                    {
                        "date": "April 19, 2022",
                        "duration": 90,
                        "minTideFeet": -1.055,
                        "minTideTime": "2022-04-19T07:30:00.000Z",
                        "people": 2,
                        "start": "2022-04-19T07:00:00.000Z",
                        "end": "2022-04-19T08:30:00.000Z",
                        "dawn": "2022-04-19T06:02:00.000Z",
                        "dusk": "2022-04-19T20:16:46.000Z",
                    }
                ]
            )
        },
    )
    assert response.status_code == 302
    assert Shift.objects.count() == 1
    shift = Shift.objects.get()
    assert shift.shift_start.isoformat() == "2022-04-19T07:00:00+00:00"
    assert shift.shift_end.isoformat() == "2022-04-19T08:30:00+00:00"
    assert shift.dawn.isoformat() == "2022-04-19T06:02:00+00:00"
    assert shift.dusk.isoformat() == "2022-04-19T20:16:46+00:00"
    assert shift.mllw_feet == pytest.approx(-1.055)
    assert shift.lowest_tide.isoformat() == "2022-04-19T07:30:00+00:00"
    assert shift.target_stewards == 2
