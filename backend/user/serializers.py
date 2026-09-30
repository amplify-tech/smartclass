from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings

User = get_user_model()


class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Email/password login with separate messages for missing account and bad password."""

    default_error_messages = {
        'no_account': 'No account found with this email.',
        'bad_password': 'Wrong password.',
        'inactive': 'This account is inactive.',
    }

    def validate(self, attrs):
        email = (attrs.get(self.username_field) or '').strip()
        password = attrs.get('password') or ''
        user_model = get_user_model()

        try:
            user = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            raise serializers.ValidationError({'email': self.error_messages['no_account']})

        if not user.check_password(password):
            raise serializers.ValidationError({'password': self.error_messages['bad_password']})

        if not user.is_active:
            raise serializers.ValidationError({'email': self.error_messages['inactive']})

        self.user = user
        refresh = self.get_token(self.user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """Current authenticated user profile (no password)."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, default='', max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
        )
        read_only_fields = ('id',)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Account already exists.')
        return email

    def validate_first_name(self, value):
        return value.strip()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        user = User(
            email=attrs['email'],
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        validate_password(attrs['password'], user=user)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)
