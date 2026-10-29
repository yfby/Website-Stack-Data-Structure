# StudyStack — a recovery-first study planner

**StudyStack helps college students manage study tasks so they can recover
accidentally removed tasks quickly.**

Coursework arrives from several classes at once. StudyStack gives each task a
course, category, priority, due date, and status. When a task is removed by
mistake, it goes onto a real **LIFO stack**: the newest removal is restored
first, the way undo is expected to behave.

> **LIFO implementation:** [`backend/stack.py`](backend/stack.py) now uses a
> Python list as a stack. The end of the list is the top. The original FIFO
> dictionary baseline has been replaced.

This is a Flask + Jinja + HTML/CSS + SQLite project. There is one server and no
Node.js build, database server, account, or API key.

## What the website does

- Create, edit, move, remove, and restore study tasks.
- Organize tasks as **To study**, **In progress**, or **Completed**.
- Filter by status and by a concept-specific **course** field.
- Search titles, descriptions, categories, and courses.
- Switch between a three-column board and a compact list.
- See a live recovery stack with the next task clearly marked **Top**.
- Keep removed tasks' title, description, course, category, priority, due date,
  and previous status intact when they are restored.
- Use a separate local workspace per browser profile.
- Customize the workspace name and accent color.

Sample data contains **8 fictional college study records** such as linked-list
review, a lab report, an exam formula sheet, and a group presentation.

## Where the stack lives

The LIFO code is in [`backend/stack.py`](backend/stack.py). `HistoryBuffer` keeps
a list in bottom-to-top order:

```python
self._items = ["A", "B", "C"]   # C is the top
```

| Operation | Implementation | Time |
| --- | --- | --- |
| `push(item)` | `self._items.append(item)` | O(1) |
| `pop()` | `self._items.pop()` | O(1) |
| `peek()` | `self._items[-1]` | O(1) |
| `is_empty()` | `not self._items` | O(1) |
| `size()` | `len(self._items)` | O(1) |
| `to_list()` | `list(self._items)` | O(n) |

The real routes in [`backend/app.py`](backend/app.py) connect the class to the
website:

- `POST /items/<id>/remove` calls `history.push(item_id)`.
- `GET /recovery` uses `peek()`, `is_empty()`, and `size()` without removing.
- `POST /recovery/restore` calls `history.pop()` and restores that ID.
- `to_list()` is saved bottom-to-top in SQLite, then passed back to the
  constructor on the next request.

Removing A, B, then C therefore restores **C, B, A**. See
[`docs/STACK_EXPLANATION.md`](docs/STACK_EXPLANATION.md) for the full explanation.

## Project layout

```text
.
+-- frontend/
|   +-- templates/          HTML + Jinja pages
|   |   +-- base.html       Shared layout, navigation, flash notices, footer
|   |   +-- index.html      Study board, course filter, search, progress
|   |   +-- item_form.html  Add/edit task form
|   |   +-- recovery.html   LIFO recovery stack
|   |   +-- activity.html   Recent actions
|   |   +-- settings.html   Workspace name and accent
|   |   +-- guide.html      How StudyStack works
|   |   +-- error.html      Friendly error page
|   |   +-- macros.html     Icons, CSRF helper, task card
|   +-- static/
|       +-- style.css       Warm paper/teal/coral responsive design
|       +-- favicon.svg     Browser tab icon
+-- backend/
|   +-- app.py              Flask routes and validation
|   +-- config.py           Paths connecting the layers
|   +-- stack.py            LIFO recovery stack (student challenge solution)
+-- database/
|   +-- db.py               SQLite connections, queries, migration
|   +-- schema.sql          Tables for workspaces, items, events
|   +-- data/.gitkeep       Keeps the generated-data folder in Git
+-- docs/
|   +-- STACK_EXPLANATION.md
|   +-- TEST_LOG.md
|   +-- CONTRIBUTIONS.md
|   +-- STUDENT_ACTIVITY.md
|   +-- ...other starter guides
+-- tests/                  Website, layout, and static checks
+-- challenge/check_stack.py  LIFO acceptance checks
+-- run.py                  Cross-platform launcher
+-- RUN_TESTS.bat           Windows website checks
+-- CHECK_STACK.bat         Windows stack checks
+-- requirements.txt        Flask dependency
```

## Setup and run


### UV method

```powershell
uv run run.py
```

### Windows

```powershell
.\SETUP_WINDOWS.bat
.\START_WEBSITE.bat
```

Or manually:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

The browser opens at **http://127.0.0.1:5000**. Keep the terminal open and press
**Ctrl+C** to stop the server. Use `--port 5001` if port 5000 is busy.

### macOS / Linux

```bash
sh setup.sh
sh start.sh
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

## Tests

Windows:

```powershell
.\RUN_TESTS.bat
.\CHECK_STACK.bat
```

Cross-platform:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python challenge/check_stack.py
```

Current results are recorded in [`docs/TEST_LOG.md`](docs/TEST_LOG.md):

- Website/layout/security/persistence suite: **36 tests, OK**
- LIFO acceptance checker: **6 tests, OK**
- Manual A/B/C, mixed-operation, persistence, empty-tray, and record-integrity
  checks passed.
- Existing-database migration preserved all items and added the new course field
  with the default `General`.

## Changes made in this remix

### Purpose and content

- Renamed the site **StudyStack** and rewrote page copy around college study
  planning and quick recovery of accidental removals.
- Added study-specific categories: lecture review, assignment, lab report, exam
  prep, group project, reading, presentation, and career prep.
- Replaced the starter samples with 8 realistic fictional study tasks, courses,
  priorities, due dates, and statuses.

### Backend, database, and feature

- Replaced the dictionary FIFO buffer with a list-based LIFO stack while keeping
  the `HistoryBuffer` public interface and bottom-to-top storage contract.
- Added an `items.course` field. `database/schema.sql` defines it, and
  `database/db.py` performs an additive migration for existing databases.
- Added course-aware create/edit validation and a course filter on the study
  board. Search now also matches course labels.
- Kept CSRF protection, server-side validation, workspace isolation, archived
  records, transactions, and all restore behavior intact.
- Improved empty-tray handling and kept the recovery page's “next” display tied
  to `peek()`.

### Visual design and usability

- Redesigned `base.html`, `index.html`, `item_form.html`, `recovery.html`, and
  `style.css`: new responsive top navigation, warm paper background, ink-navy
  panels, teal/coral/gold accents, serif display headings, task cards, and a
  visual “top of stack” treatment.
- Added a four-metric summary strip, a semester progress bar, course filter,
  clearer stack explainer, and responsive layouts for tablet and phone widths.
- Updated the favicon to match the stacked-lines mark.

### Documentation

- Added [`docs/STACK_EXPLANATION.md`](docs/STACK_EXPLANATION.md) (FIFO baseline,
  representation, operations, complexity, persistence, and a solved bug).
- Added [`docs/TEST_LOG.md`](docs/TEST_LOG.md) with the actual check results.
- Added [`docs/CONTRIBUTIONS.md`](docs/CONTRIBUTIONS.md) as a team contribution
  template.
- Updated this README with concept, setup, tests, changes, limitations, and
  credit.

## Database migration

The starter `CREATE TABLE IF NOT EXISTS` statement cannot add a column to an
existing table. On startup, `database/db.py` checks `PRAGMA table_info(items)`
and, if needed, runs:

```sql
ALTER TABLE items ADD COLUMN course TEXT NOT NULL DEFAULT 'General';
```

No rows are dropped or rewritten. Existing tasks simply show `General` until
they are edited. New databases get the `course` column directly from
`schema.sql`.

## Known limitations

- This is a local classroom sandbox, not a production account system. Each
  browser profile gets its own workspace through a signed session cookie.
- There is no password login, shared team workspace, or cloud sync.
- The recovery history is a single ordered list per workspace; it does not offer
  multi-step redo or a separate archive browser.
- Deleting or losing the browser cookie, local SQLite file, or signing key can
  make that workspace inaccessible. Back up generated data if needed.
- The interface uses system fonts so it works offline; no external font service
  is required.
- The course filter only lists courses currently attached to active tasks.

## Credit

This project began as the **Website Stack Data Structure** classroom starter by
[franku69](https://github.com/franku69/Website-Stack-Data-Structure). The original
frontend/backend/database organization, safety checks, and activity structure
were retained and remixed into StudyStack. The recovery buffer was changed from
the provided FIFO baseline to a real LIFO stack as required by the activity.
