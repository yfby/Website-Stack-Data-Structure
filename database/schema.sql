-- DATABASE LAYER: table definitions for StudyStack.
-- Applied automatically by database/db.py when the app starts.
-- CREATE IF NOT EXISTS preserves existing tables and records.
-- database/db.py applies small additive migrations (for example, the course
-- column introduced by the StudyStack remix) so existing local databases keep
-- their records.

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'My workspace',
    accent TEXT NOT NULL DEFAULT 'pine',
    history_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    course TEXT NOT NULL DEFAULT 'General',
    category TEXT NOT NULL DEFAULT 'General',
    status TEXT NOT NULL DEFAULT 'todo'
        CHECK(status IN ('todo', 'doing', 'done')),
    priority TEXT NOT NULL DEFAULT 'medium'
        CHECK(priority IN ('low', 'medium', 'high')),
    due_date TEXT,
    archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0, 1)),
    removed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_workspace_idx
    ON items(workspace_id, archived, status);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_workspace_idx ON events(workspace_id, id);
