from django.urls import path

from user.views import RegisterView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
]
