import os
from functools import wraps
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-to-a-random-string-in-production")

WATCH_TOKEN = os.environ.get("WATCH_TOKEN", "change-this-to-a-secret-watch-token")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def ensure_db():
    database.init_db()


# ── Pages ─────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    food = database.get_food_today(user_id)
    workout = database.get_workout_today(user_id)
    sleep = database.get_sleep_recent(user_id)
    weight = database.get_weight_history(user_id)
    watch = database.get_watch_calories_today(user_id)
    return render_template(
        "index.html",
        username=session["username"],
        food=food,
        workout=workout,
        sleep=sleep,
        weight=weight,
        watch=watch,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = database.get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    conn = database.get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    if count > 0:
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("register.html", error="Username and password required")
        pw_hash = generate_password_hash(password)
        conn = database.get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?,?)",
                (username, pw_hash),
            )
            conn.commit()
        except Exception:
            conn.close()
            return render_template("register.html", error="Username already taken")
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Food API ──────────────────────────────────────────────────

@app.route("/api/food", methods=["POST"])
@login_required
def api_food_add():
    data = request.json or {}
    user_id = session["user_id"]
    name = data.get("name", "")
    calories = int(data.get("calories", 0))
    protein = int(data.get("protein", 0))
    time = datetime.now().strftime("%H:%M")
    database.add_food(user_id, time, name, calories, protein)
    return jsonify({"ok": True})


@app.route("/api/food/<int:food_id>", methods=["DELETE"])
@login_required
def api_food_delete(food_id):
    database.delete_food(session["user_id"], food_id)
    return jsonify({"ok": True})


# ── Workout API ───────────────────────────────────────────────

@app.route("/api/workout", methods=["POST"])
@login_required
def api_workout_add():
    data = request.json or {}
    user_id = session["user_id"]
    exercise = data.get("exercise", "")
    sets = int(data.get("sets", 0))
    reps = int(data.get("reps", 0))
    time = datetime.now().strftime("%H:%M")
    database.add_workout(user_id, time, exercise, sets, reps)
    return jsonify({"ok": True})


@app.route("/api/workout/<int:workout_id>", methods=["DELETE"])
@login_required
def api_workout_delete(workout_id):
    database.delete_workout(session["user_id"], workout_id)
    return jsonify({"ok": True})


# ── Sleep API ─────────────────────────────────────────────────

@app.route("/api/sleep", methods=["POST"])
@login_required
def api_sleep_add():
    data = request.json or {}
    user_id = session["user_id"]
    bedtime = data.get("bedtime", "")
    waketime = data.get("waketime", "")
    try:
        bed = datetime.strptime(bedtime, "%H:%M")
        wake = datetime.strptime(waketime, "%H:%M")
        diff = wake - bed
        hours = diff.total_seconds() / 3600
        if hours < 0:
            hours += 24
        hours = round(hours, 1)
    except Exception:
        hours = 0.0
    database.add_sleep(user_id, bedtime, waketime, hours)
    return jsonify({"ok": True})


@app.route("/api/sleep/<int:sleep_id>", methods=["DELETE"])
@login_required
def api_sleep_delete(sleep_id):
    database.delete_sleep(session["user_id"], sleep_id)
    return jsonify({"ok": True})


# ── Weight API ────────────────────────────────────────────────

@app.route("/api/weight", methods=["POST"])
@login_required
def api_weight_add():
    data = request.json or {}
    user_id = session["user_id"]
    value = float(data.get("value", 0))
    database.add_weight(user_id, value)
    return jsonify({"ok": True})


@app.route("/api/weight/<int:weight_id>", methods=["DELETE"])
@login_required
def api_weight_delete(weight_id):
    database.delete_weight(session["user_id"], weight_id)
    return jsonify({"ok": True})


# ── Watch API ─────────────────────────────────────────────────

@app.route("/api/watch/today", methods=["GET"])
@login_required
def api_watch_today():
    watch = database.get_watch_calories_today(session["user_id"])
    return jsonify(watch if watch else {})


@app.route("/api/watch/sync", methods=["POST"])
def api_watch_sync():
    token = request.headers.get("X-Watch-Token", "")
    if token != WATCH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    active = int(data.get("active_calories", 0))
    resting = int(data.get("resting_calories", 0))
    synced_at = datetime.now().strftime("%H:%M")
    # single-user app: sync is always for user 1
    database.upsert_watch_calories(1, active, resting, synced_at)
    return jsonify({"ok": True})


if __name__ == "__main__":
    database.init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
