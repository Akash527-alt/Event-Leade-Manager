def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_lead(client, make_lead):
    lead = make_lead()
    assert lead["id"] > 0
    assert lead["status"] == "not_contacted"

    fetched = client.get(f"/api/leads/{lead['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "asha@acme.com"


def test_create_trims_whitespace(client):
    response = client.post(
        "/api/leads",
        json={"name": "  Ravi  ", "company": " Zeta ", "email": "ravi@zeta.io", "event": " Expo "},
    )
    assert response.status_code == 201
    body = response.json()
    assert (body["name"], body["company"], body["event"]) == ("Ravi", "Zeta", "Expo")
    assert body["notes"] == ""


def test_create_validation_errors(client):
    bad_email = client.post(
        "/api/leads", json={"name": "A", "company": "B", "email": "nope", "event": "E"}
    )
    assert bad_email.status_code == 422

    blank_name = client.post(
        "/api/leads", json={"name": "   ", "company": "B", "email": "a@b.co", "event": "E"}
    )
    assert blank_name.status_code == 422

    bad_status = client.post(
        "/api/leads",
        json={"name": "A", "company": "B", "email": "a@b.co", "event": "E", "status": "weird"},
    )
    assert bad_status.status_code == 422


def test_update_lead_partial(client, make_lead):
    lead = make_lead()
    response = client.put(f"/api/leads/{lead['id']}", json={"status": "contacted"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "contacted"
    assert body["name"] == "Asha Rao"  # untouched fields stay as they were


def test_update_rejects_null_and_missing(client, make_lead):
    lead = make_lead()
    assert client.put(f"/api/leads/{lead['id']}", json={"name": None}).status_code == 422
    assert client.put("/api/leads/9999", json={"status": "closed"}).status_code == 404


def test_delete_lead(client, make_lead):
    lead = make_lead()
    assert client.delete(f"/api/leads/{lead['id']}").status_code == 204
    assert client.get(f"/api/leads/{lead['id']}").status_code == 404
    assert client.delete(f"/api/leads/{lead['id']}").status_code == 404


def test_list_search_and_filter(client, make_lead):
    make_lead(name="Asha Rao", company="Acme Corp", event="SaaStr 2026")
    make_lead(name="Ben Cole", company="Globex", email="ben@globex.com", event="Web Summit",
              status="contacted", notes="Loves our pricing page")
    make_lead(name="Chitra Nair", company="Initech", email="chitra@initech.com",
              event="Web Summit", status="replied", notes="Needs SOC2 info")

    everything = client.get("/api/leads").json()
    assert everything["total"] == 3

    by_name = client.get("/api/leads", params={"search": "asha"}).json()
    assert [l["name"] for l in by_name["items"]] == ["Asha Rao"]

    by_notes = client.get("/api/leads", params={"search": "soc2"}).json()
    assert [l["name"] for l in by_notes["items"]] == ["Chitra Nair"]

    by_status = client.get("/api/leads", params={"status": "contacted"}).json()
    assert by_status["total"] == 1 and by_status["items"][0]["name"] == "Ben Cole"

    by_event = client.get("/api/leads", params={"event": "Web Summit"}).json()
    assert by_event["total"] == 2

    combined = client.get(
        "/api/leads", params={"event": "Web Summit", "status": "replied", "search": "chitra"}
    ).json()
    assert combined["total"] == 1

    assert client.get("/api/leads", params={"status": "bogus"}).status_code == 422


def test_list_is_newest_first_and_paginated(client, make_lead):
    for i in range(3):
        make_lead(name=f"Person {i}", email=f"p{i}@x.com")
    page = client.get("/api/leads", params={"limit": 2}).json()
    assert page["total"] == 3
    assert [l["name"] for l in page["items"]] == ["Person 2", "Person 1"]


def test_events_endpoint(client, make_lead):
    make_lead(event="Zebra Con")
    make_lead(event="Alpha Expo", email="b@b.com")
    make_lead(event="Alpha Expo", email="c@c.com")
    assert client.get("/api/events").json() == ["Alpha Expo", "Zebra Con"]
