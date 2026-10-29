# Test log — StudyStack LIFO and website remix

**Date:** 2026-10-29  
**Environment:** Linux, Python 3.14.7, Flask 3.1.3  
**Project root:** folder containing `run.py`

Windows students can use `RUN_TESTS.bat` and `CHECK_STACK.bat`; this log records
the equivalent commands with the local `.venv` interpreter.

## Summary

| Check | Command | Result |
| --- | --- | --- |
| Website, layout, validation, persistence | `.venv/bin/python -m unittest discover -s tests -v` | **36 tests, OK** |
| Required LIFO stack checks | `.venv/bin/python challenge/check_stack.py` | **6 tests, OK** |
| Manual stack and route demonstration | inline Python script (below) | **All assertions passed** |
| Existing-database migration | copy of `database/data/workbench.sqlite3` | **6 items preserved; `course` added with default `General`** |

## 1. Basic LIFO order

```text
A,B,C pushed -> to_list: ['A', 'B', 'C']
peek: C size: 3
restore order: C, B, A
```

Result: **PASS**. Removing A, B, C stores them bottom-to-top, and restoration
returns C, B, A.

## 2. Peek without removal

Called `peek()` repeatedly on a stack of A, B, C:

```text
next before restoring: C
next before restoring: C
```

Result: **PASS**. The top stayed C and the size remained 3.

## 3. Mixed operations

Direct class check:

```text
mixed pop: B
mixed rest: C A empty: True
```

Real route check:

```text
mixed next after restoring B2: A2
mixed next after removing C2: C2
mixed after C2 restore, next: A2
mixed after A2 restore, next: Your stack is clear
```

Sequence: remove A2 and B2 → restore B2 → remove C2 → restore C2 → restore A2.
Result: **PASS**. The order was C2 then A2 after the intermediate restore.

## 4. Persistence after reload

Direct check:

```text
persistence saved list: ['A', 'B', 'C'] reloaded pop: C
```

Route check used a fresh request for every restore and reloaded the stack from
SQLite each time. The saved history was:

```text
saved history (bottom -> top): [9, 10, 11]
```

C was restored first, then B, then A. Result: **PASS**. The list survives the
database round trip in bottom-to-top order.

## 5. Empty recovery tray

```text
empty tray message present: True
```

The page showed “The recovery tray is empty” and a restore POST still returned
HTTP 303 with no exception. The automated test
`test_empty_restore_is_safe` also passed. Result: **PASS**.

## 6. Record integrity

Each restored task kept its original fields:

```text
restored C: archived=0, course=CS 210 · Data Structures, status=doing, priority=high, due=2027-03-01
restored B: archived=0, course=CS 210 · Data Structures, status=doing, priority=high, due=2027-03-01
restored A: archived=0, course=CS 210 · Data Structures, status=doing, priority=high, due=2027-03-01
```

The script also asserted the original description was unchanged. Result:
**PASS**. Title, description, course, category, priority, due date, and previous
status all survived remove/restore.

## 7. Database migration check

An existing starter database was copied to a temporary location before running
the app. The before/after check produced:

```text
course before: False
course after: True
items preserved: 6 -> 6
default values: ['General']
```

Result: **PASS**. Existing rows were preserved and received the safe default
course label.

## 8. Automated website checks

The full test run ended with:

```text
Ran 36 tests in 2.940s

OK
```

The stack checker ended with:

```text
Ran 6 tests in 0.187s

OK

All Stack goal checks passed. Demonstrate and explain your solution too.
```

## Presentation-test expectation changes

The redesign changed only presentation expectations tied to the remixed starter;
no validation, security, isolation, or persistence assertion was weakened.

| Test | Before | After | Reason |
| --- | --- | --- | --- |
| `test_main_pages_and_both_views_render` | Looks for `workbench` | Looks for `StudyStack` | New site name |
| `test_sample_data_is_seeded_only_once` | Expects 6 sample items | Expects 8 sample items | New concept-specific seed data |
| `test_empty_title_and_invalid_values_are_rejected` | Expects 6 total items after rejected posts | Expects 8 total items | Same seed count change |
| `test_sql_like_input_stays_data` | Expects 7 total items after one add | Expects 9 total items | Same seed count change |
| `test_course_field_survives_save_and_filters_the_board` | Not present | Added | Verifies the new course field/filter feature |

All original checks for CSRF protection, validation, workspace isolation,
escaping, transactions, and persistence remain in place and pass.
