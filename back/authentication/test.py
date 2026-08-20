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
            "first_name": "Atra",
            "last_name": "Soufi",
            "phone": "09120000000",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="atra@example.com")
        self.assertEqual(user.first_name, "Atra")
        self.assertEqual(user.last_name, "Soufi")
        self.assertEqual(user.phone, "09120000000")
        self.assertEqual(response.data["user"]["phone"], "09120000000")

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


class MeAPITestCase(APITestCase):
    url = "/api/auth/me/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="atra@example.com",
            username="atra",
            password="StrongPassword123!",
            first_name="Atra",
            last_name="Soufi",
            phone="09120000000",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_authenticated_user_can_get_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "atra@example.com")
        self.assertEqual(response.data["username"], "atra")
        self.assertEqual(response.data["first_name"], "Atra")
        self.assertEqual(response.data["last_name"], "Soufi")
        self.assertEqual(response.data["phone"], "09120000000")
        self.assertIn("id", response.data)
        self.assertIn("date_joined", response.data)

    def test_user_can_update_profile(self):
        payload = {
            "first_name": "NewName",
            "last_name": "NewLast",
            "phone": "09350000000",
        }
        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "NewName")
        self.assertEqual(response.data["last_name"], "NewLast")
        self.assertEqual(response.data["phone"], "09350000000")

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "NewName")
        self.assertEqual(self.user.phone, "09350000000")

    def test_unauthenticated_user_cannot_get_profile(self):
        self.client.credentials()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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

    def test_password_reset_request_sends_html_email(self):
        response = self.client.post(
            self.request_url,
            {"email": "atra@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn("Password Reset", email.subject)
        self.assertTrue(email.alternatives)
        html_body, content_type = email.alternatives[0]
        self.assertEqual(content_type, "text/html")
        self.assertIn("Reset Password", html_body)
        self.assertIn("atra", html_body)

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
