"""Integration tests for Flask routes in app.py."""
import json
import pytest
from werkzeug.security import generate_password_hash

import database
import app as flask_app


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the database module at a fresh temp file for every test."""
    db_file = str(tmp_path / "test_cuttrack.db")
    monkeypatch.setattr(database, "DB", db_file)
    database.init_db()


@pytest.fixture()
def client(isolated_db):
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app.test_client() as c:
        yield c


def _register_and_login(client, username="alice", password="secret"):
    """Helper: create a user directly and log in via POST /login."""
    uid = _create_user(username, password)
    resp = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    return uid, resp


def _create_user(username="alice", password="secret"):
    conn = database.get_db()
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?,?)",
        (username, generate_password_hash(password)),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return row["id"]


# ── Auth routes ───────────────────────────────────────────────

def test_redirect_unauthenticated_to_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_register_first_user(client):
    resp = client.post(
        "/register",
        data={"username": "bob", "password": "pass123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # After register, redirected to login (no user is logged in yet)
    assert b"SIGN IN" in resp.data or b"login" in resp.data.lower()


def test_register_locked_after_first_user(client):
    _create_user("alice", "secret")
    resp = client.get("/register", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_valid_credentials(client):
    _create_user("alice", "secret")
    resp = client.post(
        "/login",
        data={"username": "alice", "password": "secret"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_login_invalid_credentials(client):
    _create_user("alice", "secret")
    resp = client.post(
        "/login",
        data={"username": "alice", "password": "wrong"},
        follow_redirects=True,
    )
    assert b"Invalid" in resp.data


def test_logout(client):
    _register_and_login(client)
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    # Accessing / after logout should redirect to login
    resp2 = client.get("/", follow_redirects=False)
    assert resp2.status_code == 302


# ── Food API ──────────────────────────────────────────────────

def test_api_food_add(client):
    _register_and_login(client)
    resp = client.post(
        "/api/food",
        data=json.dumps({"name": "Eggs", "calories": 150, "protein": 12}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json["ok"] is True


def test_api_food_add_requires_login(client):
    resp = client.post(
        "/api/food",
        data=json.dumps({"name": "Eggs", "calories": 150, "protein": 12}),
        content_type="application/json",
    )
    assert resp.status_code == 302


def test_api_food_delete(client):
    uid, _ = _register_and_login(client)
    database.add_food(uid, "08:00", "Oats", 200, 8)
    food_id = database.get_food_today(uid)[0]["id"]
    resp = client.delete(f"/api/food/{food_id}")
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    assert database.get_food_today(uid) == []


# ── Workout API ───────────────────────────────────────────────

def test_api_workout_add(client):
    _register_and_login(client)
    resp = client.post(
        "/api/workout",
        data=json.dumps({"exercise": "Pushups", "sets": 3, "reps": 20}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json["ok"] is True


def test_api_workout_delete(client):
    uid, _ = _register_and_login(client)
    database.add_workout(uid, "07:00", "Pullups", 3, 10)
    w_id = database.get_workout_today(uid)[0]["id"]
    resp = client.delete(f"/api/workout/{w_id}")
    assert resp.status_code == 200
    assert database.get_workout_today(uid) == []


# ── Sleep API ─────────────────────────────────────────────────

def test_api_sleep_add(client):
    uid, _ = _register_and_login(client)
    resp = client.post(
        "/api/sleep",
        data=json.dumps({"bedtime": "23:00", "waketime": "07:00"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    rows = database.get_sleep_recent(uid)
    assert len(rows) == 1
    assert rows[0]["hours"] == 8.0


def test_api_sleep_overnight_hours(client):
    """Bedtime after midnight should still compute positive hours."""
    uid, _ = _register_and_login(client)
    client.post(
        "/api/sleep",
        data=json.dumps({"bedtime": "22:00", "waketime": "06:00"}),
        content_type="application/json",
    )
    rows = database.get_sleep_recent(uid)
    assert rows[0]["hours"] == 8.0


def test_api_sleep_delete(client):
    uid, _ = _register_and_login(client)
    database.add_sleep(uid, "23:00", "07:00", 8.0)
    s_id = database.get_sleep_recent(uid)[0]["id"]
    resp = client.delete(f"/api/sleep/{s_id}")
    assert resp.status_code == 200
    assert database.get_sleep_recent(uid) == []


# ── Weight API ────────────────────────────────────────────────

def test_api_weight_add(client):
    uid, _ = _register_and_login(client)
    resp = client.post(
        "/api/weight",
        data=json.dumps({"value": 163.5}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    rows = database.get_weight_history(uid)
    assert rows[0]["value"] == 163.5


def test_api_weight_delete(client):
    uid, _ = _register_and_login(client)
    database.add_weight(uid, 163.0)
    w_id = database.get_weight_history(uid)[0]["id"]
    resp = client.delete(f"/api/weight/{w_id}")
    assert resp.status_code == 200
    assert database.get_weight_history(uid) == []


# ── Watch API ─────────────────────────────────────────────────

def test_api_watch_today_empty(client):
    _register_and_login(client)
    resp = client.get("/api/watch/today")
    assert resp.status_code == 200
    assert resp.json == {}


def test_api_watch_sync_valid_token(client):
    _create_user("alice", "secret")
    resp = client.post(
        "/api/watch/sync",
        data=json.dumps({"active_calories": 400, "resting_calories": 1800}),
        content_type="application/json",
        headers={"X-Watch-Token": flask_app.WATCH_TOKEN},
    )
    assert resp.status_code == 200
    assert resp.json["ok"] is True


def test_api_watch_sync_invalid_token(client):
    resp = client.post(
        "/api/watch/sync",
        data=json.dumps({"active_calories": 400, "resting_calories": 1800}),
        content_type="application/json",
        headers={"X-Watch-Token": "wrong-token"},
    )
    assert resp.status_code == 401


def test_api_watch_today_after_sync(client):
    uid, _ = _register_and_login(client)
    database.upsert_watch_calories(uid, 350, 1750, "12:00")
    resp = client.get("/api/watch/today")
    assert resp.status_code == 200
    data = resp.json
    assert data["active_calories"] == 350
    assert data["resting_calories"] == 1750
