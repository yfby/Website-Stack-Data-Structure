"""BACKEND / STUDENT MODIFICATION ZONE: backend/stack.py.

This module implements the recovery tray as a real LIFO Stack.

Representation
--------------
``self._items`` is a Python list kept in bottom-to-top order:

* index 0 is the oldest removed item (the bottom of the stack)
* the last index is the newest removed item (the top of the stack)

Because every operation works at the end of the list, ``push``, ``pop``,
``peek``, and ``size`` are O(1). ``to_list`` copies the whole list, so it is
O(n) and preserves the bottom-to-top order the database stores.

Storage contract: to_list() returns values from oldest/bottom to newest/top.
The database saves that list and passes it to the constructor next request.
"""


class HistoryBuffer:
    """A LIFO stack of removed item IDs.

    The public name is kept for ``backend/app.py`` and ``challenge/check_stack.py``.
    """

    def __init__(self, items=None):
        # Copy the input so the stack owns its storage and never mutates the
        # caller's list. Saved values arrive in bottom-to-top order.
        self._items = list(items) if items is not None else []

    def push(self, item):
        """Add one removed item's ID to the top of the stack."""
        self._items.append(item)

    def pop(self):
        """Remove and return the top (most recently pushed) item ID."""
        if self.is_empty():
            raise IndexError("The recovery tray is empty.")
        return self._items.pop()

    def peek(self):
        """Return the top item ID without removing it."""
        if self.is_empty():
            raise IndexError("The recovery tray is empty.")
        return self._items[-1]

    def is_empty(self):
        """True when there are no recovery records."""
        return not self._items

    def size(self):
        """Number of recovery records."""
        return len(self._items)

    def to_list(self):
        """Return a NEW list in bottom-to-top order, ready to save in SQLite."""
        return list(self._items)
