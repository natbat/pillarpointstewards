def test_homepage(client):
    response = client.get("/")
    html = response.content.decode("utf-8")
    assert "<title>Pillar Point Tidepool Stewards</title>" in html
