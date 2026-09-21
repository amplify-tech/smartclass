from django.urls import path

from user.views import ProfileView, RegisterView

urlpatterns = [
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/register/', RegisterView.as_view(), name='register'),
]
