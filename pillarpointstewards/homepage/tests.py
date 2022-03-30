def test_homepage(client):
    response = client.get("/")
    html = response.content.decode("utf-8")
    assert "<title>Pillar Point Tidepool Stewards</title>" in html
    assert ">Coming soon!<" in html


def test_homepage_logged_in(admin_client):
    response = admin_client.get("/")
    html = response.content.decode("utf-8")
    assert ">Coming soon!<" not in html
