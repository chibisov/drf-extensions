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


class CustomRegexUserViewSet(ModelViewSet):
    lookup_value_regex = 'a'
    model = UserModel


class CustomRegexGroupViewSet(ModelViewSet):
    lookup_value_regex = 'b'
    model = GroupModel


class CustomRegexPermissionViewSet(ModelViewSet):
    lookup_value_regex = 'c'
    model = PermissionModel
