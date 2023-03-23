from django.contrib.auth import get_user_model, authenticate
from djoser.compat import get_user_email_field_name
from djoser.conf import settings
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import EmailField, ModelSerializer, RegexField, CharField, BooleanField
from djoser.serializers import UserCreateSerializer, TokenCreateSerializer

from users.models import UserSubscription

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
        user = self.context['request'].user
        is_subscribed = UserSubscription.objects.filter(user=user, following=obj.id).exists()
        return is_subscribed


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


