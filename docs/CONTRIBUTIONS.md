# Contributions — StudyStack

Complete this file before submitting. Replace the placeholder rows with one row
per team member. Each person should be able to explain the files and behavior
they contributed, not only list a task name.

## Team

| Member | Main role | Files / areas changed | What this member can explain | Evidence |
| --- | --- | --- | --- | --- |
| Member 1 — [Name] | Stack implementation | `backend/stack.py` | List-as-stack representation, LIFO order, O(1)/O(n) complexity, empty handling | `CHECK_STACK` run + A/B/C demonstration |
| Member 2 — [Name] | Backend integration | `backend/app.py`, `database/db.py`, `database/schema.sql` | push/pop/peek route flow, SQLite persistence order, course migration | Remove/restore demo + migration check |
| Member 3 — [Name] | Frontend design | `frontend/templates/*.html`, `frontend/static/style.css` | Layout, responsive breakpoints, recovery-stack visualization, accessibility choices | Screenshots on desktop and narrow screen |
| Member 4 — [Name] | Content, docs, testing | `README.md`, `docs/*`, `tests/test_website.py` | StudyStack concept, sample data, test commands, changed expectations | `RUN_TESTS` output + `docs/TEST_LOG.md` |

Delete unused rows or add more rows if the team is larger or smaller.

## Contribution notes

Use this space to describe how the team divided the work and reviewed one
another's changes.

- Coordination / review:
- Shared decisions:
- Pairing or handoff notes:
- Remaining limitations:

## Individual explanation checklist

Each member should be ready to answer:

1. Which file did you change, and what problem did it solve?
2. Why is the end of the Python list the top of the stack?
3. Why are `push`, `pop`, `peek`, and `size` O(1)?
4. Why is `to_list()` O(n), and why must it return a new list?
5. How does SQLite keep the bottom-to-top order after a reload?
6. Where does the real site call `push()`, `peek()`, and `pop()`?
7. What happens when the recovery tray is empty?
8. Which test or demonstration proves your contribution works?

## Academic integrity

List any outside tutorials, documentation, or AI assistance used, following your
instructor's policy. The source of the original starter is credited in the root
`README.md`.
