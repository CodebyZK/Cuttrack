import csv
import io
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    add_food,
    add_food_on_date,
    add_sleep,
    add_weight,
    add_workout,
    count_users,
    create_user,
    delete_food,
    delete_sleep,
    delete_weight,
    delete_workout,
    get_all_weight_history,
    get_first_user,
    get_food_history,
    get_food_today,
    get_sleep_recent,
    get_user_by_username,
    get_watch_calories_today,
    get_weight_history,
    get_workout_history,
    get_workout_today,
    init_db,
    upsert_watch_calories,
)

app = Flask(__name__)
app.secret_key = os.environ.get("CUTTRACK_SECRET_KEY", "change-this-to-a-random-string-in-production")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
WATCH_TOKEN = os.environ.get("CUTTRACK_WATCH_TOKEN", "change-this-to-a-secret-watch-token")
OLLAMA_URL = os.environ.get("CUTTRACK_OLLAMA_URL", "")
OLLAMA_MODEL = os.environ.get("CUTTRACK_OLLAMA_MODEL", "llama3.2")

TARGET_CALORIES = 1400
TARGET_PROTEIN = 140
TARGET_SLEEP_MIN = 7
TARGET_SLEEP_MAX = 9
GOAL_WEIGHT = 145
START_WEIGHT = 165


init_db()


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def current_user_id():
    return session.get("user_id")


def parse_sleep_hours(bedtime, waketime):
    bed_dt = datetime.strptime(bedtime, "%H:%M")
    wake_dt = datetime.strptime(waketime, "%H:%M")
    if wake_dt <= bed_dt:
        wake_dt += timedelta(days=1)
    return round((wake_dt - bed_dt).total_seconds() / 3600.0, 2)


@app.route("/")
def root():
    if count_users() == 0:
        return redirect(url_for("register"))
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("index"))


@app.route("/index")
@login_required
def index():
    user_id = current_user_id()
    food = get_food_today(user_id)
    workout = get_workout_today(user_id)
    sleep = get_sleep_recent(user_id, limit=7)
    weight = get_weight_history(user_id, limit=30)
    watch = get_watch_calories_today(user_id)

    return render_template(
        "index.html",
        username=session.get("username", "user"),
        food=food,
        workout=workout,
        sleep=sleep,
        weight=weight,
        watch=watch,
        targets={
            "calories": TARGET_CALORIES,
            "protein": TARGET_PROTEIN,
            "sleep_min": TARGET_SLEEP_MIN,
            "sleep_max": TARGET_SLEEP_MAX,
            "goal_weight": GOAL_WEIGHT,
            "start_weight": START_WEIGHT,
        },
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if count_users() > 0:
        return redirect(url_for("login"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            error = "Username and password are required."
        else:
            user_id = create_user(username, generate_password_hash(password))
            session.permanent = True
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if count_users() == 0:
        return redirect(url_for("register"))

    if "user_id" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = get_user_by_username(username)

        if not user or not check_password_hash(user["password_hash"], password):
            error = "Invalid username or password."
        else:
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/food", methods=["POST"])
@login_required
def api_food_add():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    calories = int(data.get("calories") or 0)
    protein = int(data.get("protein") or 0)

    if not name:
        return json_error("Food name is required.")

    add_food(current_user_id(), datetime.now().strftime("%H:%M"), name, calories, protein)
    return jsonify({"ok": True})


@app.route("/api/food/<int:food_id>", methods=["DELETE"])
@login_required
def api_food_delete(food_id):
    delete_food(current_user_id(), food_id)
    return jsonify({"ok": True})


@app.route("/api/workout", methods=["POST"])
@login_required
def api_workout_add():
    data = request.get_json(silent=True) or {}
    exercise = (data.get("exercise") or "").strip()
    sets = int(data.get("sets") or 0)
    reps = int(data.get("reps") or 0)

    if not exercise:
        return json_error("Exercise is required.")

    add_workout(current_user_id(), datetime.now().strftime("%H:%M"), exercise, sets, reps)
    return jsonify({"ok": True})


@app.route("/api/workout/<int:workout_id>", methods=["DELETE"])
@login_required
def api_workout_delete(workout_id):
    delete_workout(current_user_id(), workout_id)
    return jsonify({"ok": True})


@app.route("/api/sleep", methods=["POST"])
@login_required
def api_sleep_add():
    data = request.get_json(silent=True) or {}
    bedtime = data.get("bedtime") or ""
    waketime = data.get("waketime") or ""

    if not bedtime or not waketime:
        return json_error("Both bedtime and waketime are required.")

    try:
        hours = parse_sleep_hours(bedtime, waketime)
    except ValueError:
        return json_error("Invalid time format.")

    add_sleep(current_user_id(), bedtime, waketime, hours)
    return jsonify({"ok": True, "hours": hours})


@app.route("/api/sleep/<int:sleep_id>", methods=["DELETE"])
@login_required
def api_sleep_delete(sleep_id):
    delete_sleep(current_user_id(), sleep_id)
    return jsonify({"ok": True})


@app.route("/api/weight", methods=["POST"])
@login_required
def api_weight_add():
    data = request.get_json(silent=True) or {}

    try:
        value = float(data.get("value"))
    except (TypeError, ValueError):
        return json_error("Weight must be a number.")

    add_weight(current_user_id(), value)
    return jsonify({"ok": True})


@app.route("/api/weight/<int:weight_id>", methods=["DELETE"])
@login_required
def api_weight_delete(weight_id):
    delete_weight(current_user_id(), weight_id)
    return jsonify({"ok": True})


@app.route("/api/watch/today", methods=["GET"])
@login_required
def api_watch_today():
    watch = get_watch_calories_today(current_user_id())
    if not watch:
        return jsonify(
            {
                "ok": True,
                "active_calories": 0,
                "resting_calories": 0,
                "synced_at": None,
            }
        )

    return jsonify(
        {
            "ok": True,
            "active_calories": watch["active_calories"],
            "resting_calories": watch["resting_calories"],
            "synced_at": watch["synced_at"],
        }
    )


@app.route("/api/watch/sync", methods=["POST"])
def api_watch_sync():
    provided = request.headers.get("X-Watch-Token", "")
    if not WATCH_TOKEN or provided != WATCH_TOKEN:
        return json_error("Unauthorized watch sync token.", status=401)

    user = get_first_user()
    if not user:
        return json_error("No registered user exists yet.", status=400)

    data = request.get_json(silent=True) or {}

    try:
        active = int(data.get("active_calories") or 0)
        resting = int(data.get("resting_calories") or 0)
    except (TypeError, ValueError):
        return json_error("Calorie fields must be integers.")

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    upsert_watch_calories(user["id"], active, resting, synced_at)

    return jsonify(
        {
            "ok": True,
            "active_calories": active,
            "resting_calories": resting,
            "synced_at": synced_at,
        }
    )


@app.route("/food")
@login_required
def food_page():
    user_id = current_user_id()
    food = get_food_history(user_id, days=7)
    food_chart = get_food_history(user_id, days=30)
    return render_template("food.html", food=food, food_chart=food_chart, ollama_enabled=bool(OLLAMA_URL), targets={"calories": TARGET_CALORIES, "protein": TARGET_PROTEIN})


@app.route("/workout")
@login_required
def workout_page():
    user_id = current_user_id()
    workout = get_workout_history(user_id, days=30)
    return render_template("workout.html", workout=workout)


@app.route("/sleep")
@login_required
def sleep_page():
    user_id = current_user_id()
    sleep = get_sleep_recent(user_id, limit=30)
    sleep_chart = list(reversed(sleep[:14]))
    return render_template(
        "sleep.html",
        sleep=sleep,
        sleep_chart=sleep_chart,
        targets={"sleep_min": TARGET_SLEEP_MIN, "sleep_max": TARGET_SLEEP_MAX},
    )


@app.route("/weight")
@login_required
def weight_page():
    user_id = current_user_id()
    weight = get_all_weight_history(user_id)
    return render_template(
        "weight.html",
        weight=weight,
        targets={"goal_weight": GOAL_WEIGHT, "start_weight": START_WEIGHT},
    )


@app.route("/api/food/lookup", methods=["POST"])
@login_required
def api_food_lookup():
    if not OLLAMA_URL:
        return json_error("Ollama not configured. Set CUTTRACK_OLLAMA_URL.", status=503)

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return json_error("Food name is required.")

    prompt = (
        f'Estimate calories and protein for: "{name}". '
        'Output ONLY a JSON object: {"calories": 350, "protein": 30}. '
        'Use integers. No other text.'
    )
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())

        text = result.get("response", "")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return json_error("Could not parse Ollama response.")

        nutrition = json.loads(text[start:end])
        return jsonify({
            "ok": True,
            "calories": int(nutrition.get("calories", 0)),
            "protein": int(nutrition.get("protein", 0)),
        })
    except urllib.error.URLError as e:
        return json_error(f"Could not reach Ollama: {e.reason}", status=503)
    except (json.JSONDecodeError, KeyError, ValueError):
        return json_error("Could not parse Ollama response.")


@app.route("/api/import/cronometer", methods=["POST"])
@login_required
def api_import_cronometer():
    if "file" not in request.files:
        return json_error("No file provided.")

    f = request.files["file"]
    content = f.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))

    imported = 0
    for i, row in enumerate(reader):
        if i >= 2000:
            break
        try:
            day = row.get("Day", "").strip()
            name = row.get("Food Name", "").strip()
            cal_str = (row.get("Energy (kcal)", "") or "0").strip()
            prot_str = (row.get("Protein (g)", "") or "0").strip()

            if not day or not name:
                continue

            datetime.strptime(day, "%Y-%m-%d")
            calories = int(float(cal_str or 0))
            protein = int(float(prot_str or 0))
            add_food_on_date(current_user_id(), day, "00:00", name, calories, protein)
            imported += 1
        except (ValueError, KeyError):
            continue

    return jsonify({"ok": True, "imported": imported})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
