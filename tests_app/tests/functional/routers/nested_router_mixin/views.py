# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.decorators import action, link

from .models import (
    NestedRouterMixinUserModel,
    NestedRouterMixinGroupModel,
    NestedRouterMixinPermissionModel,
)
from .serializers import (
    UserSerializer,
    GroupSerializer,
    PermissionSerializer,
)


class UserViewSet(NestedViewSetMixin, ModelViewSet):
    model = NestedRouterMixinUserModel
    serializer_class = UserSerializer

    @action(endpoint='users-list-action', is_for_list=True)
    def users_list_action(self, request, *args, **kwargs):
        return Response('users list action')

    @action(endpoint='users-action')
    def users_action(self, request, *args, **kwargs):
        return Response('users action')


class GroupViewSet(NestedViewSetMixin, ModelViewSet):
    model = NestedRouterMixinGroupModel
    serializer_class = GroupSerializer

    @link(endpoint='groups-list-link', is_for_list=True)
    def groups_list_link(self, request, *args, **kwargs):
        return Response('groups list link')

    @link(endpoint='groups-link')
    def groups_link(self, request, *args, **kwargs):
        return Response('groups link')


class PermissionViewSet(NestedViewSetMixin, ModelViewSet):
    model = NestedRouterMixinPermissionModel
    serializer_class = PermissionSerializer

    @action(endpoint='permissions-list-action', is_for_list=True)
    def permissions_list_action(self, request, *args, **kwargs):
        return Response('permissions list action')

    @action(endpoint='permissions-action')
    def permissions_action(self, request, *args, **kwargs):
        return Response('permissions action')