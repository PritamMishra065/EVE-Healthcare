from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = "/api/auth/signup/"
        self.login_url = "/api/auth/login/"
        self.profile_url = "/api/auth/profile/"

    def test_signup_success(self):
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
        }
        resp = self.client.post(self.signup_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["email"], "test@example.com")
        self.assertNotIn("password", resp.data)

    def test_signup_duplicate_email(self):
        User.objects.create_user(email="dup@example.com", username="dup", password="Pass123!")
        resp = self.client.post(self.signup_url, {
            "email": "dup@example.com",
            "username": "dup2",
            "password": "StrongPass123!",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_weak_password(self):
        resp = self.client.post(self.signup_url, {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(email="login@example.com", username="loginuser", password="Pass123!")
        resp = self.client.post(self.login_url, {
            "email": "login@example.com",
            "password": "Pass123!",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        User.objects.create_user(email="bad@example.com", username="baduser", password="Pass123!")
        resp = self.client.post(self.login_url, {
            "email": "bad@example.com",
            "password": "wrong",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_unauthenticated(self):
        resp = self.client.get(self.profile_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated(self):
        user = User.objects.create_user(email="me@example.com", username="me", password="Pass123!")
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.profile_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "me@example.com")
