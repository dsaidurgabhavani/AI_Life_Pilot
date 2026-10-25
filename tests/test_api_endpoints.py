import os
import sys
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import database
import models
from routers import external, reminders, assistant, tasks

class TestApiRouterEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_01_external_weather_endpoint(self):
        res = external.get_weather_endpoint(location="Vijayawada")
        self.assertTrue(res.success)
        self.assertEqual(res.city, "Vijayawada")
        self.assertIsNotNone(res.temperature_c)
        self.assertIn("Open-Meteo", res.source)

    def test_02_external_search_endpoint(self):
        res = external.web_search_endpoint(q="latest AI developments", limit=3)
        self.assertTrue(res.success)
        self.assertGreater(len(res.results), 0)
        self.assertTrue(res.results[0].url.startswith("http"))

    def test_03_external_calendar_ics_export(self):
        res = external.export_calendar_ics()
        self.assertEqual(res.media_type, "text/calendar")
        self.assertIn(b"BEGIN:VCALENDAR", res.body)
        self.assertIn(b"END:VCALENDAR", res.body)

    def test_04_reminders_crud_endpoints(self):
        # Create reminder
        create_payload = models.ReminderCreate(
            title="Review Algorithms Chapter 5",
            remind_at="2026-10-27T10:00:00",
            channel="in_app"
        )
        created = reminders.create_reminder(create_payload)
        self.assertEqual(created.status, "pending")
        self.assertEqual(created.title, "Review Algorithms Chapter 5")
        rem_id = created.id

        # List reminders
        listed = reminders.list_reminders(status="pending", limit=50)
        self.assertTrue(any(r.id == rem_id for r in listed))

        # Update reminder
        updated = reminders.update_reminder(rem_id, models.ReminderUpdate(status="sent"))
        self.assertEqual(updated.status, "sent")

        # Delete reminder
        deleted = reminders.delete_reminder(rem_id)
        self.assertEqual(deleted["id"], rem_id)

    def test_05_assistant_chat_endpoint_examples(self):
        # Example 1: Create task
        res1 = assistant.handle_chat(models.ChatMessageRequest(
            message="Create a task to finish my Java assignment tomorrow"
        ))
        self.assertIn("✅", res1.reply)
        self.assertEqual(res1.engine_used, "real_action_engine")

        # Example 2: Live weather
        res2 = assistant.handle_chat(models.ChatMessageRequest(
            message="What is the weather in Vijayawada right now?"
        ))
        self.assertIn("Vijayawada", res2.reply)
        self.assertIn("Temperature", res2.reply)

        # Example 3: Live web search
        res3 = assistant.handle_chat(models.ChatMessageRequest(
            message="Search for the latest AI developments"
        ))
        self.assertIn("http", res3.reply)

    def test_06_document_summarization_endpoint(self):
        req = models.DocumentSummaryRequest(
            text="AI LifePilot integrates live weather from Open-Meteo and web search via DuckDuckGo. Tasks are persisted to SQLite database.",
            title="Architecture Brief"
        )
        res = assistant.handle_summarize_document(req)
        self.assertEqual(res.title, "Architecture Brief")
        self.assertGreater(len(res.key_points), 0)
        self.assertGreater(len(res.suggested_tasks), 0)

if __name__ == "__main__":
    unittest.main()
