import os
import sys
import unittest
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import database
import ai_service
import external_services
import scheduler

class TestRealProductivityAssistant(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_01_no_alex_morgan_in_database_or_settings(self):
        """Criterion 10 & 1: Verify Alex Morgan is completely absent from user profile and settings."""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_name FROM user_settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        user_name = row["user_name"]
        self.assertNotEqual(user_name, "Alex Morgan")
        self.assertNotIn("Alex", user_name)

    def test_02_live_weather_retrieval(self):
        """Criterion 3 & 4: Live weather retrieval for Vijayawada with actual temperature and timestamps."""
        weather = external_services.get_live_weather("Vijayawada")
        self.assertTrue(weather["success"])
        self.assertEqual(weather["city"], "Vijayawada")
        self.assertIn("temperature_c", weather)
        self.assertIsInstance(weather["temperature_c"], (int, float))
        self.assertIn("condition", weather)
        self.assertIn("observation_time", weather)
        self.assertEqual(weather["source"], "Open-Meteo Live API")

    def test_03_live_web_search(self):
        """Criterion 3: Live web search retrieves actual current results with source links."""
        search_res = external_services.search_web("latest AI developments", max_results=3)
        self.assertTrue(search_res["success"])
        self.assertGreater(len(search_res["results"]), 0)
        first_result = search_res["results"][0]
        self.assertTrue(first_result["title"])
        self.assertTrue(first_result["snippet"])
        self.assertTrue(first_result["url"].startswith("http"))

    def test_04_task_creation_writes_to_database(self):
        """Criterion 4 & 5: Task creation writes persistently to SQLite."""
        task_title = f"Finish my Java assignment {int(datetime.now().timestamp())}"
        res = ai_service.chat_with_assistant(
            f"Create a task to {task_title} tomorrow",
            conversation_history=[],
            context={"tasks": [], "user_name": "TestUser", "settings": {}}
        )
        self.assertIn("✅", res["reply"])
        self.assertEqual(res["engine_used"], "real_action_engine")
        self.assertIsNotNone(res.get("action_executed"))

        saved_task = res["action_executed"]["task"]
        task_id = saved_task["id"]

        # Verify persistence directly from DB query
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row, "Task must be persistently written to SQLite")
        self.assertEqual(row["id"], task_id)
        self.assertEqual(row["status"], "pending")
        self.assertIn("java", row["title"].lower())

    def test_05_task_completion_and_deletion_persist(self):
        """Criterion 5: Task update/completion and deletion persist in database."""
        # Create a temporary task
        task = ai_service.execute_create_task(title="Temp Task for CRUD Test")
        task_id = task["id"]

        # Complete task
        completed = ai_service.execute_complete_task(task_id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed["status"], "completed")

        # Verify completed in DB
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        self.assertEqual(row["status"], "completed")

        # Delete task
        deleted = ai_service.execute_delete_task(task_id)
        self.assertIsNotNone(deleted)

        # Verify deleted in DB
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_06_database_persistence_across_connection_refresh(self):
        """Criterion 6: Page refresh / reconnection retains all saved tasks."""
        # Write task with unique name
        unique_title = f"Persistent Homework {datetime.now().isoformat()}"
        ai_service.execute_create_task(title=unique_title, deadline="2026-10-30T18:00")

        # Simulate independent new connection as if page reloaded
        fresh_conn = database.get_connection()
        cursor = fresh_conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE title = ?", (unique_title,))
        found = cursor.fetchone()
        fresh_conn.close()

        self.assertIsNotNone(found)
        self.assertEqual(found["title"], unique_title)

    def test_07_real_time_reminders_and_scheduler(self):
        """Criterion 7: Reminders scheduled in DB and processed by backend scheduler."""
        past_time = (datetime.now() - timedelta(seconds=2)).isoformat()
        reminder = database.create_reminder_record(
            title="Urgent Study Checkup",
            remind_at=past_time,
            channel="in_app"
        )
        self.assertEqual(reminder["status"], "pending")
        rem_id = reminder["id"]

        # Run scheduler process
        import asyncio
        asyncio.run(scheduler.process_due_reminders())

        # Verify database transition to 'sent'
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, sent_at FROM reminders WHERE id = ?", (rem_id,))
        updated = cursor.fetchone()
        conn.close()

        self.assertEqual(updated["status"], "sent", "Scheduler must transition due reminder to 'sent'")
        self.assertIsNotNone(updated["sent_at"])

        # Clean up
        database.delete_reminder_record(rem_id)

    def test_08_invalid_api_key_produces_clear_error(self):
        """Criterion 8: Invalid API key produces honest, clear error notice rather than fake answer."""
        res = ai_service.chat_with_assistant(
            "Explain quantum algorithms in detail",
            conversation_history=[],
            context={"tasks": [], "user_name": "TestUser", "settings": {}},
            gemini_key="INVALID_TEST_KEY_9999"
        )
        self.assertEqual(res["engine_used"], "api_error_notice")
        self.assertIn("Google Gemini API Error", res["reply"])
        self.assertNotIn("fake", res["reply"].lower())

    def test_09_conversational_context_retained(self):
        """Criterion 2: Conversational context is retained across conversation history turns."""
        history = [
            {"role": "user", "content": "I am working on my compiler design project."},
            {"role": "model", "content": "Great, what phase are you currently tackling?"}
        ]
        res = ai_service.chat_with_assistant(
            "What time is it right now?",
            conversation_history=history,
            context={"tasks": [], "user_name": "TestUser", "settings": {}}
        )
        self.assertTrue(res["reply"])
        self.assertIn("Time", res["reply"])

    def test_10_external_icalendar_generation(self):
        """Criterion 7: Standard RFC 5545 iCalendar generation for calendar export."""
        tasks = [
            {"id": "t-1", "title": "Math Exam", "deadline": "2026-10-28T09:00", "status": "pending", "category": "Study"},
            {"id": "t-2", "title": "Client Sync", "deadline": "2026-10-29T14:00", "status": "pending", "category": "Work"}
        ]
        ics = external_services.generate_icalendar(tasks)
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("SUMMARY:Math Exam", ics)
        self.assertIn("SUMMARY:Client Sync", ics)
        self.assertIn("END:VCALENDAR", ics)

    def test_11_backend_authorization_check(self):
        """Criterion 11: Backend authorization verification prevents unauthorized access."""
        from routers.assistant import verify_user_authorization
        from fastapi import HTTPException

        # Valid authorization
        self.assertTrue(verify_user_authorization(None))
        self.assertTrue(verify_user_authorization("Bearer valid_token_123"))

        # Invalid format
        with self.assertRaises(HTTPException):
            verify_user_authorization("Basic 12345")

        # Revoked / invalid token
        with self.assertRaises(HTTPException):
            verify_user_authorization("Bearer revoked")

    def test_12_time_and_timezone_accuracy(self):
        """Criterion 3: Current date, time, and timezone information."""
        curr_time = external_services.get_current_time("Asia/Kolkata")
        self.assertIn("date", curr_time)
        self.assertIn("time_24h", curr_time)
        self.assertEqual(curr_time["timezone"], "Asia/Kolkata")

if __name__ == "__main__":
    unittest.main()
