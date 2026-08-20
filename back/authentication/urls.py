from django.urls import path

from .views import HealthCheckView, RegisterView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("auth/register/", RegisterView.as_view(), name="register"),
]
