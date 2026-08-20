from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)


class HealthCheckView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "authentication-api",
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "Registration successful.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  body: {"email": "...", "password": "..."}"""

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/  body: {"refresh": "<refresh_token>"}"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset/  body: {"email": "..."}"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        # Always return the same message (security: do not leak user existence)
        if result:
            user = result["user"]
            uid = result["uid"]
            token = result["token"]

            frontend_url = getattr(
                settings, "FRONTEND_URL", "http://localhost:5173"
            )
            reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"

            send_mail(
                subject="Password Reset Request",
                message=(
                    f"Hi {user.username},\n\n"
                    f"You requested a password reset. Click the link below:\n\n"
                    f"{reset_link}\n\n"
                    f"If you did not request this, ignore this email.\n"
                ),
                from_email=getattr(
                    settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
                ),
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response(
            {
                "message": (
                    "If an account with that email exists, "
                    "a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
