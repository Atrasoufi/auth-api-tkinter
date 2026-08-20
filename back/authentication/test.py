from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


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


class LoginAPITestCase(APITestCase):
    url = "/api/auth/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="atra@example.com",
            username="atra",
            password="StrongPassword123!",
        )

    def test_user_can_login(self):
        payload = {
            "email": "atra@example.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "atra@example.com")

    def test_login_with_wrong_password_fails(self):
        payload = {
            "email": "atra@example.com",
            "password": "WrongPassword123!",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutAPITestCase(APITestCase):
    url = "/api/auth/logout/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="atra@example.com",
            username="atra",
            password="StrongPassword123!",
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}"
        )

    def test_user_can_logout(self):
        response = self.client.post(
            self.url,
            {"refresh": str(self.refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)


class ChangePasswordAPITestCase(APITestCase):
    url = "/api/auth/change-password/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="atra@example.com",
            username="atra",
            password="OldPassword123!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_user_can_change_password(self):
        payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewStrongPassword123!",
            "new_password_confirm": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123!"))

    def test_wrong_old_password_is_rejected(self):
        payload = {
            "old_password": "WrongOldPassword!",
            "new_password": "NewStrongPassword123!",
            "new_password_confirm": "NewStrongPassword123!",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetAPITestCase(APITestCase):
    request_url = "/api/auth/password-reset/"
    confirm_url = "/api/auth/password-reset/confirm/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="atra@example.com",
            username="atra",
            password="OldPassword123!",
        )

    def test_password_reset_request_sends_email(self):
        response = self.client.post(
            self.request_url,
            {"email": "atra@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password Reset", mail.outbox[0].subject)

    def test_password_reset_request_unknown_email_still_ok(self):
        response = self.client.post(
            self.request_url,
            {"email": "unknown@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)

        payload = {
            "uid": uid,
            "token": token,
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        }
        response = self.client.post(self.confirm_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPassword123!"))

    def test_password_reset_confirm_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        payload = {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        }
        response = self.client.post(self.confirm_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
