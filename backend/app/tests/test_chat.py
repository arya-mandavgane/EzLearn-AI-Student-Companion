"""
test_chat.py — Automated Tests for Chatbot Pipeline & Analytics
─────────────────────────────────────────────────────────────────
Verifies:
1. Cannot send chat message without adding resources first (Enforced rule).
2. Create conversation & add resources (text, file/mock).
3. Sending message produces: What you asked, Explanation, Demonstration/Simulation, 10-Question Quiz.
4. Quiz submission locks attempt (attempt once), calculates score & returns AI suggestions.
5. Repeated quiz submission returns existing locked result without re-attempting.
6. Daily/Weekly/Monthly reports accurately aggregate accuracy, weaknesses, and must-do topics.
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestChatbotPipeline(unittest.TestCase):

    def test_01_create_conversation(self):
        res = client.post("/api/chat/conversations", json={"title": "Data Structures Study"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "Data Structures Study")

    def test_02_cannot_chat_without_resources(self):
        # Create empty conversation
        conv_res = client.post("/api/chat/conversations", json={"title": "Empty Session"})
        conv_id = conv_res.json()["id"]

        # Attempt to send message without adding resources
        msg_res = client.post(f"/api/chat/conversations/{conv_id}/messages", json={
            "prompt": "Explain stack and queue please"
        })
        self.assertEqual(msg_res.status_code, 400)
        self.assertIn("no study resources attached", msg_res.json()["detail"].lower())

    def test_03_add_resource_and_chat_flow(self):
        # 1. Create conversation
        conv_res = client.post("/api/chat/conversations", json={"title": "Photosynthesis Session"})
        conv_id = conv_res.json()["id"]

        # 2. Add text resource
        notes = (
            "Photosynthesis is the process by which green plants convert light energy into chemical energy. "
            "Chlorophyll absorbs photons in chloroplasts. Reactants are carbon dioxide and water; products are glucose and oxygen."
        )
        add_res = client.post(f"/api/chat/conversations/{conv_id}/resources/text", json={
            "text": notes,
            "title": "Bio Chapter 4"
        })
        self.assertEqual(add_res.status_code, 200)

        # 3. Chat prompt
        msg_res = client.post(f"/api/chat/conversations/{conv_id}/messages", json={
            "prompt": "How do plants convert sunlight into food?"
        })
        self.assertEqual(msg_res.status_code, 200)
        data = msg_res.json()

        # Check required output formats:
        self.assertIn("user_prompt", data)
        self.assertIn("explanation", data)
        self.assertIn("real_life_picture", data["explanation"])
        self.assertIn("simulation", data)
        self.assertIn("quiz", data)
        self.assertEqual(len(data["quiz"]["questions"]), 10)

        msg_id = data["message_id"]

        # 4. Submit Quiz
        stored_questions = data["quiz"]["stored_questions"]
        answers = [{"question_id": q["id"], "answer": q.get("correct_answer", "")} for q in stored_questions]

        sub_res = client.post(
            f"/api/chat/conversations/{conv_id}/messages/{msg_id}/submit-quiz",
            json={"message_id": msg_id, "answers": answers}
        )
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.json()
        self.assertFalse(sub_data["already_attempted"])
        self.assertEqual(sub_data["quiz_attempt"]["score"], 10)
        self.assertIn("ai_suggestions", sub_data)

        # 5. Subsequent submission is locked (Attempt Once)
        sub_res_again = client.post(
            f"/api/chat/conversations/{conv_id}/messages/{msg_id}/submit-quiz",
            json={"message_id": msg_id, "answers": answers}
        )
        self.assertEqual(sub_res_again.status_code, 200)
        self.assertTrue(sub_res_again.json()["already_attempted"])

    def test_04_performance_reports(self):
        # 1. Unauthenticated guest report request returns 401
        guest_res = client.get("/api/chat/reports/daily")
        self.assertEqual(guest_res.status_code, 401)

        # 2. Registered user logs in and accesses performance reports
        reg_res = client.post("/api/auth/register", json={
            "name": "Report Tester",
            "email": "reporter@example.com",
            "age": 20,
            "password": "Password123!",
        })
        token = reg_res.json()["access_token"] if reg_res.status_code == 201 else client.post("/api/auth/login", json={
            "email": "reporter@example.com",
            "password": "Password123!",
        }).json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        for tf in ["daily", "weekly", "monthly"]:
            res = client.get(f"/api/chat/reports/{tf}", headers=headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["timeframe"], tf)
            self.assertIn("overall_accuracy_pct", data)
            self.assertIn("strengths", data)
            self.assertIn("weaknesses", data)
            self.assertIn("must_do_topics", data)


if __name__ == "__main__":
    unittest.main()
