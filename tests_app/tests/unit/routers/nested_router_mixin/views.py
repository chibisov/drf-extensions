# -*- coding: utf-8 -*-
from rest_framework.viewsets import ModelViewSet

from .models import (
    UnitNestedRouterMixinUserModel as UserModel,
    UnitNestedRouterMixinGroupModel as GroupModel,
    UnitNestedRouterMixinPermissionModel as PermissionModel,
)


class UserViewSet(ModelViewSet):
    model = UserModel


class GroupViewSet(ModelViewSet):
    model = GroupModel


class PermissionViewSet(ModelViewSet):
    model = PermissionModel

