# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.decorators import action, link

from .models import (
    NestedRouterMixinUserModel as UserModel,
    NestedRouterMixinGroupModel as GroupModel,
    NestedRouterMixinPermissionModel as PermissionModel,
    NestedRouterMixinTaskModel as TaskModel,
    NestedRouterMixinBookModel as BookModel,
    NestedRouterMixinCommentModel as CommentModel
)
from .serializers import (
    UserSerializer,
    GroupSerializer,
    PermissionSerializer,
    TaskSerializer,
    BookSerializer,
    CommentSerializer
)


class UserViewSet(NestedViewSetMixin, ModelViewSet):
    model = UserModel
    serializer_class = UserSerializer

    @action(endpoint='users-list-action', is_for_list=True)
    def users_list_action(self, request, *args, **kwargs):
        return Response('users list action')

    @action(endpoint='users-action')
    def users_action(self, request, *args, **kwargs):
        return Response('users action')


class GroupViewSet(NestedViewSetMixin, ModelViewSet):
    model = GroupModel
    serializer_class = GroupSerializer

    @link(endpoint='groups-list-link', is_for_list=True)
    def groups_list_link(self, request, *args, **kwargs):
        return Response('groups list link')

    @link(endpoint='groups-link')
    def groups_link(self, request, *args, **kwargs):
        return Response('groups link')


class PermissionViewSet(NestedViewSetMixin, ModelViewSet):
    model = PermissionModel
    serializer_class = PermissionSerializer

    @action(endpoint='permissions-list-action', is_for_list=True)
    def permissions_list_action(self, request, *args, **kwargs):
        return Response('permissions list action')

    @action(endpoint='permissions-action')
    def permissions_action(self, request, *args, **kwargs):
        return Response('permissions action')


class TaskViewSet(NestedViewSetMixin, ModelViewSet):
    model = TaskModel
    serializer_class = TaskSerializer


class BookViewSet(NestedViewSetMixin, ModelViewSet):
    model = BookModel
    serializer_class = BookSerializer


class CommentViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer


class TaskCommentViewSet(CommentViewSet):
    def get_queryset(self):
        return super(TaskCommentViewSet, self).get_queryset().filter(
            content_type=ContentType.objects.get_for_model(TaskModel)
        )


class BookCommentViewSet(CommentViewSet):
    def get_queryset(self):
        return super(BookCommentViewSet, self).get_queryset().filter(
            content_type=ContentType.objects.get_for_model(BookModel)
        )