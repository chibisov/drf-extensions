# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import KeyConstructorUserModel as UserModel


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
