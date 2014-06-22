# -*- coding: utf-8 -*-
from rest_framework.viewsets import ModelViewSet

from .models import (
    UnitNesterRouterMixinUserModel as UseModel,
    UnitNesterRouterMixinGroupModel as GroupModel,
    UnitNesterRouterMixinPermissionModel as PermissionModel,
)


class UserViewSet(ModelViewSet):
    model = UseModel


class GroupViewSet(ModelViewSet):
    model = GroupModel


class PermissionViewSet(ModelViewSet):
    model = PermissionModel

