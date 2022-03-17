def test_homepage(client):
    response = client.get("/")
    assert response.content.decode("utf-8").strip() == "<h1>This is the homepage</h1>"
