# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import (
    NesterRouterMixinUserModel,
    NesterRouterMixinGroupModel,
    NesterRouterMixinPermissionModel,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NesterRouterMixinUserModel
        fields = (
            'id',
            'name'
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NesterRouterMixinGroupModel
        fields = (
            'id',
            'name'
        )


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NesterRouterMixinPermissionModel
        fields = (
            'id',
            'name'
        )