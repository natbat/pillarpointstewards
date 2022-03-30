def test_homepage(client):
    response = client.get("/")
    html = response.content.decode("utf-8")
    assert "<title>Pillar Point Tidepool Stewards</title>" in html
    assert ">Coming soon!<" in html


def test_homepage_logged_in(admin_client):
    response = admin_client.get("/")
    html = response.content.decode("utf-8")
    assert ">Coming soon!<" not in html
    assert response.context["upcoming_shifts"] == []


def test_homepage_shows_assigned_shifts(admin_client, admin_user_has_shift):
    response = admin_client.get("/")
    assert len(response.context["upcoming_shifts"]) == 1
