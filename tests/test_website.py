"""Checks for the provided app. These do not require the Stack goal to be solved."""

import json
import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from database import db
from backend.stack import HistoryBuffer


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = {"TESTING": True, "SECRET_KEY": "website-tests-only",
                       "DATABASE": str(Path(self.directory.name) / "test.sqlite3")}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.client.get("/")

    def tearDown(self):
        self.directory.cleanup()

    def workspace_id(self, client=None):
        with (client or self.client).session_transaction() as session:
            return session["workspace_id"]

    def token(self, client=None):
        with (client or self.client).session_transaction() as session:
            return session["csrf_token"]

    def post(self, path, values=None, client=None):
        client = client or self.client
        return client.post(path, data={"csrf_token": self.token(client), **(values or {})})

    def fields(self, **changes):
        return {"title": "My test idea", "description": "A useful description.",
                "category": "General", "status": "todo", "priority": "medium",
                "due_date": "2027-01-15", **changes}

    def add(self, title, **changes):
        response = self.post("/items/new", self.fields(title=title, **changes))
        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            return db.get_db().execute("SELECT id FROM items WHERE workspace_id=? AND title=? ORDER BY id DESC",
                                       (self.workspace_id(), title)).fetchone()["id"]

    def item(self, item_id):
        with self.app.app_context():
            return db.get_item(self.workspace_id(), item_id)

    def history(self):
        with self.app.app_context():
            return db.load_history(db.get_db(), self.workspace_id())

    def test_main_pages_and_both_views_render(self):
        for path in ["/", "/?view=list", "/?status=todo", "/items/new", "/recovery", "/activity", "/settings", "/guide"]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"StudyStack", response.data)
        for path in ["/static/style.css", "/static/favicon.svg"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_sample_data_is_seeded_only_once(self):
        self.client.get("/")
        self.client.get("/activity")
        with self.app.app_context():
            self.assertEqual(db.stats(self.workspace_id())["total"], 8)

    def test_create_edit_and_move_item(self):
        item_id = self.add("First draft")
        self.assertEqual(self.client.get(f"/items/{item_id}/edit").status_code, 200)
        response = self.post(f"/items/{item_id}/edit", self.fields(title="Better draft", category="Writing"))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.item(item_id)["title"], "Better draft")
        self.assertEqual(self.item(item_id)["category"], "Writing")
        self.assertEqual(self.post(f"/items/{item_id}/move", {"status": "done"}).status_code, 303)
        self.assertEqual(self.item(item_id)["status"], "done")

    def test_course_field_survives_save_and_filters_the_board(self):
        course = "CS 210 · Data Structures"
        item_id = self.add("Review graph traversal", course=course)
        self.assertEqual(self.item(item_id)["course"], course)
        self.post(f"/items/{item_id}/edit", self.fields(title="Review graph traversal", course="CS 310 · Databases"))
        self.assertEqual(self.item(item_id)["course"], "CS 310 · Databases")
        page = self.client.get("/", query_string={"course": "CS 310 · Databases", "view": "list"})
        result_table = page.data.split(b'<table class="items-table">', 1)[1].split(b'</table>', 1)[0]
        self.assertIn(b"Review graph traversal", result_table)
        self.assertNotIn(b"Review linked-list notes", result_table)

    def test_restore_uses_the_class_and_keeps_original_details(self):
        first = self.add("First", status="doing", priority="high")
        second = self.add("Second", description="Keep this exact note.", status="done")
        for item_id in [first, second]:
            self.assertEqual(self.post(f"/items/{item_id}/remove").status_code, 303)
        expected = HistoryBuffer([first, second]).peek()
        snapshot = self.item(expected)
        self.assertTrue(snapshot["archived"])
        self.assertEqual(self.history(), [first, second])
        self.assertEqual(self.client.get("/recovery").status_code, 200)
        self.assertEqual(self.post("/recovery/restore").status_code, 303)
        restored = self.item(expected)
        self.assertEqual(restored["archived"], 0)
        for field in ["id", "title", "description", "category", "status", "priority", "due_date"]:
            self.assertEqual(restored[field], snapshot[field])
        self.assertEqual(len(self.history()), 1)

    def test_empty_restore_is_safe(self):
        response = self.post("/recovery/restore")
        self.assertEqual(response.status_code, 303)
        page = self.client.get("/recovery")
        self.assertIn(b"The recovery tray is empty", page.data)
        self.assertEqual(self.history(), [])

    def test_recovery_cards_follow_removal_order_even_with_timestamp_ties(self):
        import re
        first = self.add("Created first")
        second = self.add("Created second")
        # Remove the newer database ID first, then the older ID.
        self.post(f"/items/{second}/remove")
        self.post(f"/items/{first}/remove")
        page = self.client.get("/recovery")
        shown = [int(value) for value in re.findall(rb'data-item-id="(\d+)"', page.data)]
        self.assertEqual(shown, [first, second])

    def test_second_remove_cannot_duplicate_a_history_entry(self):
        item_id = self.add("Only remove once")
        self.post(f"/items/{item_id}/remove")
        response = self.post(f"/items/{item_id}/remove")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.history(), [item_id])

    def test_empty_title_and_invalid_values_are_rejected(self):
        for changes in [{"title": "   "}, {"title": "x" * 101}, {"description": "x" * 1501},
                        {"category": ""}, {"status": "invented"}, {"priority": "urgent"},
                        {"due_date": "2027-02-31"}]:
            with self.subTest(changes=list(changes)):
                self.assertEqual(self.post("/items/new", self.fields(**changes)).status_code, 422)
        with self.app.app_context():
            self.assertEqual(db.stats(self.workspace_id())["total"], 8)

    def test_invalid_status_action_does_not_change_item(self):
        item_id = self.add("Keep my status")
        self.assertEqual(self.post(f"/items/{item_id}/move", {"status": "invalid"}).status_code, 400)
        self.assertEqual(self.item(item_id)["status"], "todo")

    def test_posts_require_valid_form_token(self):
        self.assertEqual(self.client.post("/items/new", data=self.fields()).status_code, 400)
        self.assertEqual(self.client.post("/items/new", data={**self.fields(), "csrf_token": "é"}).status_code, 400)
        stranger = self.app.test_client()
        self.assertEqual(stranger.post("/items/new", data=self.fields()).status_code, 400)

    def test_workspace_data_is_isolated(self):
        item_id = self.add("Private workspace idea")
        other = self.app.test_client()
        other.get("/")
        self.assertNotEqual(self.workspace_id(), self.workspace_id(other))
        self.assertNotIn(b"Private workspace idea", other.get("/").data)
        self.assertEqual(other.get(f"/items/{item_id}/edit").status_code, 404)
        self.assertEqual(self.post(f"/items/{item_id}/remove", client=other).status_code, 404)
        self.assertEqual(self.item(item_id)["archived"], 0)

    def test_search_filter_and_literal_wildcards(self):
        self.add("100% original idea", category="Marker", status="doing")
        self.add("Different idea", status="todo")
        page = self.client.get("/?q=Marker&status=doing&view=list")
        result_table = page.data.split(b'<table class="items-table">', 1)[1].split(b'</table>', 1)[0]
        self.assertIn(b"100% original idea", result_table)
        self.assertNotIn(b"Different idea", result_table)
        # The '%' character is treated literally, not as a match-everything query.
        page = self.client.get("/?q=%25&view=list")
        result_table = page.data.split(b'<table class="items-table">', 1)[1].split(b'</table>', 1)[0]
        self.assertIn(b"100% original idea", result_table)
        self.assertNotIn(b"Different idea", result_table)

    def test_user_content_is_escaped_in_html(self):
        self.add('<script>alert("hello")</script>')
        page = self.client.get("/")
        self.assertNotIn(b'<script>alert(', page.data)
        self.assertIn(b"&lt;script&gt;", page.data)

    def test_sql_like_input_stays_data(self):
        item_id = self.add("Robert'); DROP TABLE items;--")
        self.assertIn("DROP TABLE", self.item(item_id)["title"])
        with self.app.app_context():
            self.assertEqual(db.stats(self.workspace_id())["total"], 9)

    def test_workspace_preferences_persist(self):
        response = self.post("/settings", {"name": "Studio North", "accent": "plum"})
        self.assertEqual(response.status_code, 303)
        page = self.client.get("/")
        self.assertIn(b"Studio North", page.data)
        self.assertIn(b"accent-plum", page.data)
        self.assertEqual(self.post("/settings", {"name": "", "accent": "evil"}).status_code, 422)

    def test_records_and_history_survive_app_restart(self):
        first = self.add("Keep across restart")
        self.post(f"/items/{first}/remove")
        cookie = self.client.get_cookie("session")
        restarted = create_app(self.config)
        client = restarted.test_client()
        client.set_cookie("session", cookie.value)
        self.assertIn(b"Keep across restart", client.get("/recovery").data)
        response = self.post("/recovery/restore", client=client)
        self.assertEqual(response.status_code, 303)
        self.assertIn(b"Keep across restart", client.get("/").data)

    def test_health_does_not_create_a_workspace(self):
        client = self.app.test_client()
        self.assertEqual(client.get("/health").json["status"], "ok")
        self.assertIsNone(client.get_cookie("session"))

    def test_unknown_page_is_a_friendly_404(self):
        response = self.client.get("/missing-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"A small detour", response.data)

    def test_transaction_rolls_back_failed_history_operation(self):
        from unittest.mock import patch
        item_id = self.add("Keep when recovery fails")
        with patch("backend.app.HistoryBuffer.to_list", side_effect=RuntimeError("Simulated failure")):
            with self.assertRaises(RuntimeError):
                self.post(f"/items/{item_id}/remove")
        self.assertEqual(self.item(item_id)["archived"], 0)
        self.assertEqual(self.history(), [])


if __name__ == "__main__":
    unittest.main()
