import unittest
import uuid
from backend.database.sqlite import (
    detect_conversation_title,
    update_session_title,
    save_chat_record,
    get_all_sessions
)
from fastapi.testclient import TestClient
from backend.main import app

class TestConversationSessions(unittest.TestCase):
    def test_detect_conversation_title_github_repo(self):
        title = detect_conversation_title("https://github.com/techashutosh03/SYNORA.git open this")
        self.assertEqual(title, "SYNORA Repository")

    def test_detect_conversation_title_fix_code(self):
        title = detect_conversation_title("fix this code please")
        self.assertIn("Code Fix", title)

    def test_detect_conversation_title_question_prefix_cleaning(self):
        title = detect_conversation_title("Can you explain how async event loops work in Python?")
        self.assertNotIn("Can You", title)
        self.assertTrue("Event Loops" in title or "Async" in title)

    def test_detect_conversation_title_general(self):
        title = detect_conversation_title("Build a fast binary search tree in C++")
        self.assertTrue("Binary Search Tree" in title or "Tree In C++" in title)

    def test_session_lifecycle_and_api(self):
        test_sid = f"test-sess-{uuid.uuid4().hex[:8]}"
        
        # Save a chat record
        rec_id = save_chat_record(
            user_prompt="Can you explain how docker containers work?",
            final_response="Docker containers package applications...",
            task_type="chat",
            complexity="simple",
            models_used=["mock-model"],
            total_time_ms=120.0,
            orchestration_trace=[],
            session_id=test_sid
        )
        self.assertIsNotNone(rec_id)

        # Verify get_all_sessions retrieves it with an auto-detected title
        sessions = get_all_sessions(limit=50)
        found = next((s for s in sessions if s["session_id"] == test_sid), None)
        self.assertIsNotNone(found)
        self.assertNotEqual(found["title"], "Untitled Conversation")
        self.assertIn("Docker", found["title"])

        # Test API endpoints
        client = TestClient(app)
        res = client.get("/api/conversations")
        self.assertEqual(res.status_code, 200)
        convs = res.json()["conversations"]
        api_found = next((c for c in convs if c["session_id"] == test_sid), None)
        self.assertIsNotNone(api_found)
        self.assertEqual(api_found["title"], found["title"])

        # Test renaming conversation
        new_title = "Docker Architecture Guide"
        patch_res = client.patch(f"/api/conversations/{test_sid}/title", json={"title": new_title})
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["title"], new_title)

        # Verify updated in get_all_sessions
        updated_sessions = get_all_sessions(limit=50)
        up_found = next((s for s in updated_sessions if s["session_id"] == test_sid), None)
        self.assertEqual(up_found["title"], new_title)

if __name__ == "__main__":
    unittest.main()
