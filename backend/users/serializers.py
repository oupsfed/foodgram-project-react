from django.contrib.auth import get_user_model, authenticate
from djoser.compat import get_user_email_field_name
from djoser.conf import settings
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import EmailField, ModelSerializer, RegexField, CharField, BooleanField
from djoser.serializers import UserCreateSerializer, TokenCreateSerializer

User = get_user_model()


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return False


class UserRegistrationSerializer(UserCreateSerializer):
    email = EmailField(max_length=254,
                       required=True)
    username = RegexField(max_length=150,
                          regex=r'^[\w.@+-]',
                          required=True)
    first_name = CharField(max_length=150,
                           required=True)
    last_name = CharField(max_length=150,
                          required=True)

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
        )


class TokenSerializer(TokenCreateSerializer):
    password = CharField(required=False, style={"input_type": "password"})

    default_error_messages = {
        "invalid_credentials": settings.CONSTANTS.messages.INVALID_CREDENTIALS_ERROR,
        "inactive_account": settings.CONSTANTS.messages.INACTIVE_ACCOUNT_ERROR,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

        self.email_field = get_user_email_field_name(User)
        self.fields[self.email_field] = EmailField()

    def validate(self, attrs):
        password = attrs.get("password")
        email = attrs.get("email")
        self.user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )
        if not self.user:
            self.user = User.objects.filter(email=email).first()
            if self.user and not self.user.check_password(password):
                self.fail("invalid_credentials")
        if self.user and self.user.is_active:
            return attrs
        self.fail("invalid_credentials")
