# -*- coding: utf-8 -*-
from rest_framework.viewsets import ModelViewSet

from .models import (
    NestedRouterMixinUserModel as UserModel,
    NestedRouterMixinGroupModel as GroupModel,
    NestedRouterMixinPermissionModel as PermissionModel,
)


class UserViewSet(ModelViewSet):
    model = UserModel


class GroupViewSet(ModelViewSet):
    model = GroupModel


class PermissionViewSet(ModelViewSet):
    model = PermissionModel
