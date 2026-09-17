from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model — extend here instead of auth.User."""

    class Meta:
        db_table = 'users'
