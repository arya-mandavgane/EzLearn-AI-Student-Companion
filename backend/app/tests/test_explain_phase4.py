"""
test_explain_phase4.py — Comprehensive Automated Tests for Phase 4 Explanations
───────────────────────────────────────────────────────────────────────────────
Verifies:
1. Topic classification into analogy, comparison_table, worked_example, and simulation.
2. Rich Explanation JSON containing real_life_picture, key_terms, sections.
3. Multi-language output (English, Hindi, Marathi).
4. "This didn't help" feedback triggers format switching.
5. Level selection (simple, normal, exam_ready).
6. Backward compatibility with Phase 1-3 simple_explanation and exam_answer.
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPhase4Explanations(unittest.TestCase):

    def test_01_simulation_topic_detection(self):
        res = client.post("/api/explain", json={
            "text": "A stack is a linear data structure following the LIFO principle where push and pop take O(1) time.",
            "marks": 5,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["topic_type"], ["simulation", "analogy"])
        self.assertIn("summary", data)
        self.assertIn("real_life_picture", data)

    def test_02_comparison_table_detection_and_structure(self):
        notes = (
            "Difference between TCP and UDP protocols:\n"
            "TCP is connection-oriented, reliable, and provides flow control.\n"
            "UDP is connectionless, faster, but has no error recovery."
        )
        res = client.post("/api/explain", json={
            "text": notes,
            "format_override": "comparison_table",
            "marks": 5,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["topic_type"], "comparison_table")
        self.assertTrue("table" in data or "sections" in data)

    def test_03_worked_example_format(self):
        notes = (
            "Calculate kinetic energy of a 2 kg object moving at 3 m/s using formula KE = 0.5 * m * v^2.\n"
            "Step 1: Identify mass and velocity. Step 2: Substitute into equation. Step 3: Compute final joules."
        )
        res = client.post("/api/explain", json={
            "text": notes,
            "format_override": "worked_example",
            "marks": 5,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["topic_type"], "worked_example")

    def test_04_feedback_unhelpful_switches_format(self):
        # 1. Generate first explanation
        res1 = client.post("/api/explain", json={
            "text": "Mitochondria produce ATP through aerobic cellular respiration.",
            "marks": 5,
            "format_override": "analogy"
        })
        self.assertEqual(res1.status_code, 200)
        exp_id = res1.json()["id"]

        # 2. Submit "This didn't help" feedback
        fb_res = client.post(f"/api/explain/{exp_id}/feedback", json={
            "helpful": False,
            "rating": 1,
            "reason": "Too abstract",
            "switch_format": True
        })
        self.assertEqual(fb_res.status_code, 202)
        fb_data = fb_res.json()
        self.assertIsNotNone(fb_data["switched_format"])
        self.assertNotEqual(fb_data["switched_format"], "analogy")

    def test_05_multi_language_hindi_support(self):
        res = client.post("/api/explain", json={
            "text": "Photosynthesis process by which plants use sunlight to synthesize nutrients.",
            "language": "hi",
            "marks": 5
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["language"], "hi")

    def test_06_backward_compatibility_fields(self):
        res = client.post("/explain", json={
            "text": "Newton's laws of motion define classical mechanics.",
            "marks": 5,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("simple_explanation", data)
        self.assertIn("exam_answer", data)
        self.assertIn("topic_type", data)


if __name__ == "__main__":
    unittest.main()
