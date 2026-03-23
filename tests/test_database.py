"""Unit tests for database.py functions."""
import os
import tempfile
import pytest
import database


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the database module at a fresh temp file for every test."""
    db_file = str(tmp_path / "test_cuttrack.db")
    monkeypatch.setattr(database, "DB", db_file)
    database.init_db()
    yield


def _add_user(username="testuser", password_hash="hash"):
    conn = database.get_db()
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?,?)",
        (username, password_hash),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return row["id"]


# ── init_db ───────────────────────────────────────────────────

def test_init_db_creates_tables(tmp_path, monkeypatch):
    db_file = str(tmp_path / "fresh.db")
    monkeypatch.setattr(database, "DB", db_file)
    database.init_db()
    conn = database.get_db()
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert {"users", "food", "workout", "sleep", "weight", "watch_calories"} <= tables


# ── Food ──────────────────────────────────────────────────────

def test_add_and_get_food():
    uid = _add_user()
    database.add_food(uid, "12:00", "Chicken", 300, 40)
    rows = database.get_food_today(uid)
    assert len(rows) == 1
    assert rows[0]["name"] == "Chicken"
    assert rows[0]["calories"] == 300
    assert rows[0]["protein"] == 40


def test_get_food_today_empty():
    uid = _add_user()
    assert database.get_food_today(uid) == []


def test_delete_food():
    uid = _add_user()
    database.add_food(uid, "08:00", "Oats", 200, 10)
    rows = database.get_food_today(uid)
    food_id = rows[0]["id"]
    database.delete_food(uid, food_id)
    assert database.get_food_today(uid) == []


def test_delete_food_wrong_user_is_noop():
    uid1 = _add_user("u1")
    uid2 = _add_user("u2")
    database.add_food(uid1, "08:00", "Oats", 200, 10)
    food_id = database.get_food_today(uid1)[0]["id"]
    database.delete_food(uid2, food_id)  # wrong user
    assert len(database.get_food_today(uid1)) == 1


# ── Workout ───────────────────────────────────────────────────

def test_add_and_get_workout():
    uid = _add_user()
    database.add_workout(uid, "07:00", "Pushups", 3, 20)
    rows = database.get_workout_today(uid)
    assert len(rows) == 1
    assert rows[0]["exercise"] == "Pushups"
    assert rows[0]["sets"] == 3
    assert rows[0]["reps"] == 20


def test_get_workout_today_empty():
    uid = _add_user()
    assert database.get_workout_today(uid) == []


def test_delete_workout():
    uid = _add_user()
    database.add_workout(uid, "07:00", "Pullups", 3, 10)
    workout_id = database.get_workout_today(uid)[0]["id"]
    database.delete_workout(uid, workout_id)
    assert database.get_workout_today(uid) == []


# ── Sleep ─────────────────────────────────────────────────────

def test_add_and_get_sleep():
    uid = _add_user()
    database.add_sleep(uid, "23:00", "07:00", 8.0)
    rows = database.get_sleep_recent(uid)
    assert len(rows) == 1
    assert rows[0]["bedtime"] == "23:00"
    assert rows[0]["waketime"] == "07:00"
    assert rows[0]["hours"] == 8.0


def test_get_sleep_recent_empty():
    uid = _add_user()
    assert database.get_sleep_recent(uid) == []


def test_delete_sleep():
    uid = _add_user()
    database.add_sleep(uid, "22:00", "06:00", 8.0)
    sleep_id = database.get_sleep_recent(uid)[0]["id"]
    database.delete_sleep(uid, sleep_id)
    assert database.get_sleep_recent(uid) == []


def test_get_sleep_recent_limit():
    uid = _add_user()
    for i in range(10):
        database.add_sleep(uid, "23:00", "07:00", 8.0)
    rows = database.get_sleep_recent(uid, limit=3)
    assert len(rows) == 3


# ── Weight ────────────────────────────────────────────────────

def test_add_and_get_weight():
    uid = _add_user()
    database.add_weight(uid, 165.5)
    rows = database.get_weight_history(uid)
    assert len(rows) == 1
    assert rows[0]["value"] == 165.5


def test_get_weight_history_empty():
    uid = _add_user()
    assert database.get_weight_history(uid) == []


def test_delete_weight():
    uid = _add_user()
    database.add_weight(uid, 162.0)
    weight_id = database.get_weight_history(uid)[0]["id"]
    database.delete_weight(uid, weight_id)
    assert database.get_weight_history(uid) == []


def test_get_weight_history_limit():
    uid = _add_user()
    for i in range(35):
        database.add_weight(uid, 160.0 + i)
    rows = database.get_weight_history(uid, limit=10)
    assert len(rows) == 10


# ── Watch Calories ────────────────────────────────────────────

def test_upsert_and_get_watch_calories():
    uid = _add_user()
    database.upsert_watch_calories(uid, 450, 1800, "14:00")
    watch = database.get_watch_calories_today(uid)
    assert watch is not None
    assert watch["active_calories"] == 450
    assert watch["resting_calories"] == 1800


def test_get_watch_calories_today_empty():
    uid = _add_user()
    assert database.get_watch_calories_today(uid) is None


def test_watch_calories_returns_latest_sync():
    uid = _add_user()
    database.upsert_watch_calories(uid, 300, 1700, "10:00")
    database.upsert_watch_calories(uid, 500, 1900, "15:00")
    watch = database.get_watch_calories_today(uid)
    assert watch["active_calories"] == 500
    assert watch["synced_at"] == "15:00"
