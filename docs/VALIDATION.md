# Validation for StudyStack

The detailed command output, manual stack demonstration, and presentation-test
changes are recorded in [TEST_LOG.md](TEST_LOG.md).

## Checks completed

| Check | Outcome |
| --- | --- |
| Full website/layout suite | **36 tests passed** (`.venv/bin/python -m unittest discover -s tests -v`) |
| LIFO acceptance checker | **6 tests passed** (`.venv/bin/python challenge/check_stack.py`) |
| Manual A/B/C order | Restored **C, B, A** |
| Repeated `peek()` | Returned the top task without reducing the size |
| Mixed operations | Remove A/B → restore B → remove C → restored C, then A |
| Persistence | Reloaded from SQLite on every restore and kept the same top |
| Empty tray | Friendly page message and a safe redirect; no crash |
| Record integrity | Title, description, course, category, priority, due date, and status preserved |
| Existing-database migration | All 6 copied starter rows preserved; `course` added with default `General` |
| Python syntax, templates, schema | Covered by the project and structure tests |

## Checks that still depend on the presentation environment

- The Windows `.bat` launchers were not executed on Windows in this environment;
  their file structure and CRLF endings are covered by the static tests.
- Visual appearance was implemented responsively, but a human should still check
  the site in a browser at desktop and phone widths before submission.
- Browser cookie behavior and local persistence were exercised through Flask's
  test client rather than a live browser.

## Verify on the classroom computer

```powershell
.\SETUP_WINDOWS.bat
.\RUN_TESTS.bat
.\CHECK_STACK.bat
.\START_WEBSITE.bat
```

Open the website, create a task, move it across the board, remove it, refresh the
recovery page, and restore it. Repeat the A/B/C demonstration in
[STACK_EXPLANATION.md](STACK_EXPLANATION.md).

The dependency-free structural checks can also run before Flask is installed:

```text
python -m unittest discover -s tests -p test_structure_static.py -v
```
