import sqlite3
from datetime import date

DB = "cuttrack.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS food (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            name TEXT NOT NULL,
            calories INTEGER DEFAULT 0,
            protein INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS workout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            exercise TEXT NOT NULL,
            sets INTEGER DEFAULT 0,
            reps INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            bedtime TEXT NOT NULL,
            waketime TEXT NOT NULL,
            hours REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            value REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Apple Watch calorie syncs
    c.execute("""
        CREATE TABLE IF NOT EXISTS watch_calories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            synced_at TEXT NOT NULL,
            active_calories INTEGER DEFAULT 0,
            resting_calories INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

def today():
    return date.today().isoformat()

# ── Food ──────────────────────────────────────────────────────
def add_food(user_id, time, name, calories, protein):
    conn = get_db()
    conn.execute(
        "INSERT INTO food (user_id, date, time, name, calories, protein) VALUES (?,?,?,?,?,?)",
        (user_id, today(), time, name, calories, protein)
    )
    conn.commit(); conn.close()

def get_food_today(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM food WHERE user_id=? AND date=? ORDER BY time",
        (user_id, today())
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_food(user_id, food_id):
    conn = get_db()
    conn.execute("DELETE FROM food WHERE id=? AND user_id=?", (food_id, user_id))
    conn.commit(); conn.close()

# ── Workout ───────────────────────────────────────────────────
def add_workout(user_id, time, exercise, sets, reps):
    conn = get_db()
    conn.execute(
        "INSERT INTO workout (user_id, date, time, exercise, sets, reps) VALUES (?,?,?,?,?,?)",
        (user_id, today(), time, exercise, sets, reps)
    )
    conn.commit(); conn.close()

def get_workout_today(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM workout WHERE user_id=? AND date=? ORDER BY time",
        (user_id, today())
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_workout(user_id, workout_id):
    conn = get_db()
    conn.execute("DELETE FROM workout WHERE id=? AND user_id=?", (workout_id, user_id))
    conn.commit(); conn.close()

# ── Sleep ─────────────────────────────────────────────────────
def add_sleep(user_id, bedtime, waketime, hours):
    conn = get_db()
    conn.execute(
        "INSERT INTO sleep (user_id, date, bedtime, waketime, hours) VALUES (?,?,?,?,?)",
        (user_id, today(), bedtime, waketime, hours)
    )
    conn.commit(); conn.close()

def get_sleep_recent(user_id, limit=7):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sleep WHERE user_id=? ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_sleep(user_id, sleep_id):
    conn = get_db()
    conn.execute("DELETE FROM sleep WHERE id=? AND user_id=?", (sleep_id, user_id))
    conn.commit(); conn.close()

# ── Weight ────────────────────────────────────────────────────
def add_weight(user_id, value):
    conn = get_db()
    conn.execute(
        "INSERT INTO weight (user_id, date, value) VALUES (?,?,?)",
        (user_id, today(), value)
    )
    conn.commit(); conn.close()

def get_weight_history(user_id, limit=30):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM weight WHERE user_id=? ORDER BY date ASC, id ASC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_weight(user_id, weight_id):
    conn = get_db()
    conn.execute("DELETE FROM weight WHERE id=? AND user_id=?", (weight_id, user_id))
    conn.commit(); conn.close()

# ── Watch Calories ────────────────────────────────────────────
def upsert_watch_calories(user_id, active, resting, synced_at):
    """Store a new sync record for today."""
    conn = get_db()
    conn.execute(
        """INSERT INTO watch_calories (user_id, date, synced_at, active_calories, resting_calories)
           VALUES (?,?,?,?,?)""",
        (user_id, today(), synced_at, active, resting)
    )
    conn.commit(); conn.close()

def get_watch_calories_today(user_id):
    """Get the most recent sync for today."""
    conn = get_db()
    row = conn.execute(
        """SELECT * FROM watch_calories WHERE user_id=? AND date=?
           ORDER BY synced_at DESC LIMIT 1""",
        (user_id, today())
    ).fetchone()
    conn.close()
    return dict(row) if row else None
