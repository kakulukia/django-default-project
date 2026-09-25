from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
        )
        read_only_fields = ("id",)


class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, "password")

    def validate(self, attrs):
        if "password" in attrs:
            try:
                validate_password(attrs["password"], user=User(**attrs))
            except ValidationError as error:
                raise serializers.ValidationError({"password": error.messages}) from error
        return attrs

    def create(self, validated_data):
        return User.data.create_user(**validated_data)
