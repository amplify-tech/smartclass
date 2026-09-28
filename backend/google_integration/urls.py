from django.urls import path

from google_integration.views import GoogleAuthHealthView

urlpatterns = [
    path(
        'google/health/',
        GoogleAuthHealthView.as_view(),
        name='google-auth-health',
    ),
]
