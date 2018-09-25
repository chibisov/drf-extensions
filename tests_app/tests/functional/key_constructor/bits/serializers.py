from rest_framework import serializers

from .models import KeyConstructorUserModel


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyConstructorUserModel
        fields = '__all__'
