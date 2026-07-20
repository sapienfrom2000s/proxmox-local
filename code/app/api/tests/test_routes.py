def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_todo(client):
    r = client.post("/todos", json={"title": "Buy milk"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["title"] == "Buy milk"
    assert data["done"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_todo_missing_title(client):
    r = client.post("/todos", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "title is required"


def test_create_todo_no_body(client):
    r = client.post("/todos", content_type="application/json")
    assert r.status_code == 400


def test_list_todos_empty(client):
    r = client.get("/todos")
    assert r.status_code == 200
    assert r.get_json() == []


def test_list_todos(client):
    client.post("/todos", json={"title": "Buy milk"})
    client.post("/todos", json={"title": "Walk dog"})
    r = client.get("/todos")
    assert r.status_code == 200
    assert len(r.get_json()) == 2


def test_get_todo(client):
    r = client.post("/todos", json={"title": "Buy milk"})
    tid = r.get_json()["id"]
    r = client.get(f"/todos/{tid}")
    assert r.status_code == 200
    assert r.get_json()["title"] == "Buy milk"


def test_get_todo_not_found(client):
    r = client.get("/todos/nonexistent")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not found"


def test_update_todo(client):
    r = client.post("/todos", json={"title": "Buy milk"})
    tid = r.get_json()["id"]
    r = client.put(f"/todos/{tid}", json={"title": "Buy eggs", "done": True})
    assert r.status_code == 200
    data = r.get_json()
    assert data["title"] == "Buy eggs"
    assert data["done"] is True


def test_update_todo_not_found(client):
    r = client.put("/todos/nonexistent", json={"title": "test"})
    assert r.status_code == 404


def test_update_todo_missing_title(client):
    r = client.post("/todos", json={"title": "Buy milk"})
    tid = r.get_json()["id"]
    r = client.put(f"/todos/{tid}", json={})
    assert r.status_code == 400


def test_delete_todo(client):
    r = client.post("/todos", json={"title": "Buy milk"})
    tid = r.get_json()["id"]
    r = client.delete(f"/todos/{tid}")
    assert r.status_code == 204
    r = client.get(f"/todos/{tid}")
    assert r.status_code == 404


def test_delete_todo_not_found(client):
    r = client.delete("/todos/nonexistent")
    assert r.status_code == 404
