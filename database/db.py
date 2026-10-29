"""DATABASE LAYER: SQLite connections, transactions, and SQL storage helpers.

Tables: database/schema.sql
Saved data: database/data/workbench.sqlite3 (created automatically)
The backend calls these functions; frontend files never connect to SQLite.
No database server or ORM is required.

StudyStack additive migration: existing databases receive an ``items.course``
column with a safe default. No records are dropped or rewritten.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import current_app, g


SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_db():
    """One connection per request, reused until Flask closes that request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_app(app):
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    with app.app_context():
        connection = get_db()
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        migrate_schema(connection)
        connection.commit()


def migrate_schema(connection):
    """Apply additive changes that CREATE TABLE IF NOT EXISTS cannot make.

    Existing installations keep every item and workspace. The new course field
    defaults to 'General' until the user edits that task.
    """
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(items)")
    }
    if "course" not in columns:
        connection.execute(
            "ALTER TABLE items ADD COLUMN course TEXT NOT NULL DEFAULT 'General'"
        )


@contextmanager
def transaction():
    """Save the item change and recovery history together, or save neither."""
    connection = get_db()
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def workspace_exists(workspace_id):
    return get_db().execute(
        "SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)
    ).fetchone() is not None


def create_workspace(workspace_id):
    with transaction() as connection:
        connection.execute(
            "INSERT INTO workspaces (id, created_at) VALUES (?, ?)",
            (workspace_id, timestamp()),
        )
        seed_items(connection, workspace_id)
        log_event(connection, workspace_id, "created", "Your workspace is ready")


def get_workspace(workspace_id):
    return dict(get_db().execute(
        "SELECT * FROM workspaces WHERE id = ?", (workspace_id,)
    ).fetchone())


def seed_items(connection, workspace_id):
    """Eight fictional college study tasks for this browser's workspace only."""
    today = date.today()
    examples = [
        ("Review linked-list notes",
         "Redraw the pointer diagrams from Tuesday's lecture and mark the two spots that still feel fuzzy.",
         "CS 210 · Data Structures", "Lecture review", "todo", "high", 1),
        ("Draft CS 210 problem set 4",
         "Finish questions 2–5, then compare answers with the study-group notes before submitting.",
         "CS 210 · Data Structures", "Assignment", "doing", "high", 3),
        ("Write the osmosis lab report",
         "Turn the bench observations into a short results section before Friday's lab meeting.",
         "BIO 120 · Cell Biology", "Lab report", "todo", "medium", 2),
        ("Build a Calculus II formula sheet",
         "One page for series tests, convergence rules, and the worked examples from class.",
         "MATH 152 · Calculus II", "Exam prep", "todo", "high", 5),
        ("Prepare slides for the group presentation",
         "Add the three usability findings and a clean closing slide for the team review.",
         "COMM 210 · Public Speaking", "Group project", "doing", "medium", 4),
        ("Read chapters 6–8 of the psychology text",
         "Take margin notes on memory and attention, and bring two questions to seminar.",
         "PSY 101 · Intro Psychology", "Reading", "todo", "low", 7),
        ("Submit the technical-writing peer review",
         "Leave one strength and one concrete revision note for each partner.",
         "ENG 240 · Technical Writing", "Assignment", "done", "low", 0),
        ("Update the résumé for the career fair",
         "Add the database project and trim the high-school section to two lines.",
         "Career center", "Career prep", "done", "medium", -1),
    ]
    now = timestamp()
    for title, description, course, category, status, priority, days in examples:
        connection.execute(
            """INSERT INTO items
            (workspace_id, title, description, course, category, status, priority,
             due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (workspace_id, title, description, course, category, status, priority,
             (today + timedelta(days=days)).isoformat(), now, now),
        )


def list_items(workspace_id, query="", status="", archived=False, course=""):
    sql = "SELECT * FROM items WHERE workspace_id = ? AND archived = ?"
    values = [workspace_id, int(archived)]
    if query:
        literal = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND (title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\' OR category LIKE ? ESCAPE '\\' OR course LIKE ? ESCAPE '\\')"
        values.extend(["%" + literal + "%"] * 4)
    if status:
        sql += " AND status = ?"
        values.append(status)
    if course:
        sql += " AND course = ?"
        values.append(course)
    sql += " ORDER BY COALESCE(removed_at, created_at) DESC, id DESC"
    return [dict(row) for row in get_db().execute(sql, values).fetchall()]


def list_courses(workspace_id):
    """Distinct course labels for the study filter and form suggestions."""
    return [row["course"] for row in get_db().execute(
        """SELECT DISTINCT course FROM items
        WHERE workspace_id = ? AND archived = 0
        ORDER BY course COLLATE NOCASE""",
        (workspace_id,),
    ).fetchall()]


def get_item(workspace_id, item_id, archived=None):
    sql = "SELECT * FROM items WHERE id = ? AND workspace_id = ?"
    values = [item_id, workspace_id]
    if archived is not None:
        sql += " AND archived = ?"
        values.append(int(archived))
    row = get_db().execute(sql, values).fetchone()
    return dict(row) if row else None


def stats(workspace_id):
    result = {"total": 0, "todo": 0, "doing": 0, "done": 0, "archived": 0}
    for row in get_db().execute(
        "SELECT status, archived, COUNT(*) AS count FROM items WHERE workspace_id = ? GROUP BY status, archived",
        (workspace_id,),
    ):
        if row["archived"]:
            result["archived"] += row["count"]
        else:
            result[row["status"]] += row["count"]
            result["total"] += row["count"]
    result["open"] = result["todo"] + result["doing"]
    result["progress"] = round(result["done"] / result["total"] * 100) if result["total"] else 0
    return result


def load_history(connection, workspace_id):
    row = connection.execute(
        "SELECT history_json FROM workspaces WHERE id = ?", (workspace_id,)
    ).fetchone()
    values = json.loads(row["history_json"])
    if not isinstance(values, list) or any(type(value) is not int for value in values):
        raise ValueError("Invalid recovery data in the database.")
    return values


def save_history(connection, workspace_id, values):
    connection.execute(
        "UPDATE workspaces SET history_json = ? WHERE id = ?",
        (json.dumps(values), workspace_id),
    )


def log_event(connection, workspace_id, kind, title):
    connection.execute(
        "INSERT INTO events (workspace_id, kind, title, created_at) VALUES (?, ?, ?, ?)",
        (workspace_id, kind, title, timestamp()),
    )


def events(workspace_id, limit=50):
    return [dict(row) for row in get_db().execute(
        "SELECT * FROM events WHERE workspace_id = ? ORDER BY id DESC LIMIT ?",
        (workspace_id, limit),
    ).fetchall()]


# Item/workspace writes live here rather than inside browser route functions.
# The caller supplies an open transaction so item, history, and activity changes
# succeed or roll back together. Do not commit from these individual helpers.

def create_item(connection, workspace_id, values):
    """Insert a validated item and return its database ID."""
    now = timestamp()
    cursor = connection.execute(
        """INSERT INTO items (workspace_id, title, description, course, category,
        status, priority, due_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (workspace_id, values["title"], values["description"], values["course"],
         values["category"], values["status"], values["priority"],
         values["due_date"] or None, now, now),
    )
    return cursor.lastrowid


def update_item(connection, workspace_id, item_id, values):
    """Save validated changes to this workspace's active item."""
    connection.execute(
        """UPDATE items SET title=?, description=?, course=?, category=?, status=?,
        priority=?, due_date=?, updated_at=? WHERE id=? AND workspace_id=? AND archived=0""",
        (values["title"], values["description"], values["course"], values["category"],
         values["status"], values["priority"], values["due_date"] or None,
         timestamp(), item_id, workspace_id),
    )


def move_item(connection, workspace_id, item_id, status):
    """Change the status of an active item."""
    connection.execute(
        "UPDATE items SET status=?, updated_at=? WHERE id=? AND workspace_id=? AND archived=0",
        (status, timestamp(), item_id, workspace_id),
    )


def archive_item(connection, workspace_id, item_id):
    """Mark an item removed without deleting its details."""
    now = timestamp()
    connection.execute(
        "UPDATE items SET archived=1, removed_at=?, updated_at=? WHERE id=? AND workspace_id=?",
        (now, now, item_id, workspace_id),
    )


def restore_item(connection, workspace_id, item_id):
    """Restore the ID chosen by backend/stack.py; SQL does not choose the order."""
    connection.execute(
        "UPDATE items SET archived=0, removed_at=NULL, updated_at=? WHERE id=? AND workspace_id=?",
        (timestamp(), item_id, workspace_id),
    )


def update_workspace(connection, workspace_id, name, accent):
    """Save validated workspace preferences."""
    connection.execute(
        "UPDATE workspaces SET name=?, accent=? WHERE id=?", (name, accent, workspace_id)
    )
