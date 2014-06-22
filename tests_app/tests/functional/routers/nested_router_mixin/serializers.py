# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import (
    NestedRouterMixinUserModel,
    NestedRouterMixinGroupModel,
    NestedRouterMixinPermissionModel,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NestedRouterMixinUserModel
        fields = (
            'id',
            'name'
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NestedRouterMixinGroupModel
        fields = (
            'id',
            'name'
        )


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NestedRouterMixinPermissionModel
        fields = (
            'id',
            'name'
        )