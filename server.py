"""
YatraPlan - Backend Server
===========================
Stores all user data in SQLite database on your PC.
Run this file first, then open index.html in your browser.

Requirements: pip install flask flask-cors
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow browser to talk to this server

# Database file will be created in the same folder as server.py
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yatraplan.db")

# ─────────────────────────────────────────
#  Database Setup
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            phone       TEXT,
            salt        TEXT    NOT NULL,
            hash        TEXT    NOT NULL,
            created_at  INTEGER NOT NULL,
            registered_at TEXT,
            failed_attempts INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email  TEXT    NOT NULL,
            trip_data   TEXT    NOT NULL,
            created_at  INTEGER NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database ready at: {DB_PATH}")

# ─────────────────────────────────────────
#  User Routes
# ─────────────────────────────────────────

@app.route("/api/user/get", methods=["POST"])
def get_user():
    """Get a single user by email (for login)."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"user": None})

    return jsonify({"user": dict(row)})


@app.route("/api/user/register", methods=["POST"])
def register_user():
    """Register a new user."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    name  = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    salt  = data.get("salt") or ""
    hash_ = data.get("hash") or ""
    now   = int(datetime.now().timestamp() * 1000)
    registered_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    if not email or not name or not salt or not hash_:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO users (email, name, phone, salt, hash, created_at, registered_at, failed_attempts)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (email, name, phone, salt, hash_, now, registered_at)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "registered_at": registered_at})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/update", methods=["POST"])
def update_user():
    """Update user fields (e.g. failed_attempts)."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db()
    conn.execute(
        "UPDATE users SET failed_attempts = ? WHERE email = ?",
        (data.get("failed_attempts", 0), email)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/user/delete", methods=["POST"])
def delete_user():
    """Delete a user and all their trips."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db()
    conn.execute("DELETE FROM trips WHERE user_email = ?", (email,))
    conn.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/users/all", methods=["GET"])
def get_all_users():
    """Get ALL registered users (for admin panel)."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    users = {}
    for row in rows:
        u = dict(row)
        users[u["email"]] = u
    return jsonify({"users": users})

# ─────────────────────────────────────────
#  Trip Routes
# ─────────────────────────────────────────

@app.route("/api/trips/get", methods=["POST"])
def get_trips():
    """Get all trips for a user."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    conn = get_db()
    rows = conn.execute(
        "SELECT trip_data FROM trips WHERE user_email = ? ORDER BY created_at DESC",
        (email,)
    ).fetchall()
    conn.close()
    trips = [json.loads(row["trip_data"]) for row in rows]
    return jsonify({"trips": trips})


@app.route("/api/trips/save", methods=["POST"])
def save_trips():
    """Save/replace all trips for a user."""
    data = request.json
    email = (data.get("email") or "").strip().lower()
    trips = data.get("trips", [])
    now   = int(datetime.now().timestamp() * 1000)

    conn = get_db()
    conn.execute("DELETE FROM trips WHERE user_email = ?", (email,))
    for trip in trips:
        conn.execute(
            "INSERT INTO trips (user_email, trip_data, created_at) VALUES (?, ?, ?)",
            (email, json.dumps(trip), now)
        )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ─────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────

@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "db": DB_PATH})

# ─────────────────────────────────────────
#  Start
# ─────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n" + "="*50)
    print("  YatraPlan Server is RUNNING")
    print("="*50)
    print(f"  Database : {DB_PATH}")
    print(f"  API URL  : http://localhost:5000")
    print(f"  Open     : index.html in your browser")
    print("="*50)
    print("  Press Ctrl+C to stop the server\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
