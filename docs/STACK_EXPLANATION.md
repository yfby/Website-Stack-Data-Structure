# How the StudyStack recovery stack works

StudyStack's recovery feature is implemented in
[`backend/stack.py`](../backend/stack.py). The site calls that class from
[`backend/app.py`](../backend/app.py); the browser never decides the recovery
order on its own.

## 1. The original starter behavior (FIFO)

The starter `HistoryBuffer` stored removed item IDs in a dictionary:

```python
self._records = {0: "A", 1: "B", 2: "C"}
```

`pop()` found the smallest dictionary key with `min(self._records)` and removed
that entry. That is **FIFO** behavior: the first item removed was the first item
restored.

If A, B, and C were removed in that order, the starter restored A first. The
dictionary also made each `pop()`/`peek()` scan the keys, so the operation was
O(n) rather than O(1).

## 2. The LIFO representation

The replacement is a Python list:

```python
self._items = ["A", "B", "C"]
```

The list is kept in **bottom-to-top** order:

```text
index 0       index 1       last index
   A             B              C
bottom        middle           top
oldest                      newest
```

The end of the list is the top of the stack. Every stack operation works at
that end, so no search or sort is needed to find the next item.

The constructor copies the incoming list:

```python
def __init__(self, items=None):
    self._items = list(items) if items is not None else []
```

That means the stack owns its storage. Changing the caller's list later cannot
change the stack.

## 3. Operations

| Method | What it does | How it works | Time |
| --- | --- | --- | --- |
| `HistoryBuffer(items=None)` | Rebuilds a stack from saved IDs in bottom-to-top order | Copies the input list | O(n) |
| `push(item)` | Adds one ID to the top | `self._items.append(item)` | O(1) amortized |
| `pop()` | Removes and returns the top ID; raises `IndexError` when empty | `self._items.pop()` | O(1) |
| `peek()` | Returns the top ID without removing it; raises `IndexError` when empty | `self._items[-1]` | O(1) |
| `is_empty()` | Reports whether the stack has no items | `not self._items` | O(1) |
| `size()` | Returns the number of items | `len(self._items)` | O(1) |
| `to_list()` | Returns a new bottom-to-top list for storage | `list(self._items)` | O(n) |

`push`, `pop`, `peek`, and `size` are constant time because they only touch the
end of the list. `to_list` must copy every item so the caller cannot mutate the
stack through the returned list, which is why it is linear time.

## 4. In-memory order versus SQLite persistence

SQLite stores the list as JSON in `workspaces.history_json` through
`db.save_history()`. The saved order is **bottom-to-top**:

```text
remove A -> ["A"]
remove B -> ["A", "B"]
remove C -> ["A", "B", "C"]   # C is the last element = top
```

On the next request, `db.load_history()` returns that list and the route rebuilds
the stack:

```python
history = HistoryBuffer(db.load_history(connection, workspace_id))
```

Because the constructor preserves the input order, C is still the top after a
page refresh or server restart. The next `pop()` returns C.

The recovery page displays cards in newest-first order for readability. That
display order is separate from the actual restore rule:

* `peek()` supplies the next task to restore.
* `pop()` supplies the ID that the restore route actually restores.
* Refreshing or viewing the page only calls `peek()`, `is_empty()`, and `size()`,
  so it never removes anything.

## 5. Route flow

```text
Remove button
  -> POST /items/<id>/remove
  -> HistoryBuffer.push(item_id)
  -> db.archive_item(...)
  -> db.save_history(history.to_list())
  -> one SQLite transaction commits

Recovery page
  -> GET /recovery
  -> HistoryBuffer(db.load_history(...))
  -> peek() for the next task
  -> is_empty() and size() for the display

Restore button
  -> POST /recovery/restore
  -> HistoryBuffer(db.load_history(...))
  -> pop() chooses the top ID
  -> db.restore_item(...) clears archived and removed_at
  -> db.save_history(history.to_list())
```

Restoring A, B, C therefore returns **C, B, A**.

## 6. A bug found and solved

The FIFO baseline could show a different “next” task from the one the page's
card order suggested. `peek()` selected the oldest ID with `min(self._records)`,
while the recovery template displayed cards by reversing the saved insertion
order. After removing A, B, and C, the newest card appeared first, but the actual
restore still chose A.

The list-based stack solved both problems at once:

* the top is unambiguously the last list element;
* `peek()` and `pop()` agree with the card labeled “Top”;
* the saved bottom-to-top list restores correct order after a reload;
* no scan or sort is needed to choose the next item.

The empty case is also handled explicitly: both `pop()` and `peek()` raise
`IndexError` rather than returning a fake value, and the restore route checks the
stack before restoring so an empty tray produces a friendly message instead of a
crash.
