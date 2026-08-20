from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterAPITestCase(APITestCase):
    url = "/api/auth/register/"

    def test_user_can_register(self):
        payload = {
            "email": "atra@example.com",
            "username": "atra",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="atra@example.com").exists())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="atra@example.com",
            username="existing",
            password="StrongPassword123!",
        )

        payload = {
            "email": "atra@example.com",
            "username": "atra2",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_must_match(self):
        payload = {
            "email": "atra@example.com",
            "username": "atra",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
