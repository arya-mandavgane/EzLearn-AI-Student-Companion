"""
test_auth.py — Unit and API tests for Phase 1 Authentication & Isolation
"""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import init_db

init_db()
client = TestClient(app)


class TestAuthAndDataIsolation(unittest.TestCase):

    def setUp(self):
        self.user_a_email = "student_a@example.com"
        self.user_a_password = "SecurePassword123!"
        self.user_b_email = "student_b@example.com"
        self.user_b_password = "AnotherPassword456!"

    def test_01_register_user_a(self):
        res = client.post(
            "/api/auth/register",
            json={
                "name": "Student A",
                "email": self.user_a_email,
                "age": 20,
                "password": self.user_a_password,
            },
        )
        # 201 Created (or 409 if already registered from earlier run)
        self.assertIn(res.status_code, [201, 409])
        if res.status_code == 201:
            data = res.json()
            self.assertIn("access_token", data)
            self.assertEqual(data["user"]["email"], self.user_a_email)
            self.assertEqual(data["user"]["age"], 20)

    def test_02_duplicate_registration_fails(self):
        # Registering again with same email must fail with 409 Conflict
        res = client.post(
            "/api/auth/register",
            json={
                "name": "Imposter",
                "email": self.user_a_email,
                "age": 22,
                "password": "AnyPassword!",
            },
        )
        self.assertEqual(res.status_code, 409)
        self.assertIn("already exists", res.json()["detail"])

    def test_03_login_wrong_password_fails(self):
        res = client.post(
            "/api/auth/login",
            json={
                "email": self.user_a_email,
                "password": "WrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Incorrect email or password", res.json()["detail"])

    def test_04_login_success(self):
        res = client.post(
            "/api/auth/login",
            json={
                "email": self.user_a_email,
                "password": self.user_a_password,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], self.user_a_email)

    def test_05_protected_route_requires_auth(self):
        # /api/auth/me without token must return 401
        res = client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_06_protected_route_with_valid_token(self):
        login_res = client.post(
            "/api/auth/login",
            json={
                "email": self.user_a_email,
                "password": self.user_a_password,
            },
        )
        token = login_res.json()["access_token"]

        me_res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_res.status_code, 200)
        profile = me_res.json()
        self.assertEqual(profile["email"], self.user_a_email)

    def test_07_user_data_isolation(self):
        # Register User B
        client.post(
            "/api/auth/register",
            json={
                "name": "Student B",
                "email": self.user_b_email,
                "age": 21,
                "password": self.user_b_password,
            },
        )
        login_b = client.post(
            "/api/auth/login",
            json={"email": self.user_b_email, "password": self.user_b_password},
        )
        token_b = login_b.json()["access_token"]

        # Check me for User B returns User B profile, NOT User A
        me_b = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(me_b.status_code, 200)
        self.assertEqual(me_b.json()["email"], self.user_b_email)
        self.assertNotEqual(me_b.json()["email"], self.user_a_email)


if __name__ == "__main__":
    unittest.main()
