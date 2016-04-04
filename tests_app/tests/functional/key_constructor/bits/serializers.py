# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import KeyConstructorUserModel


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyConstructorUserModel
