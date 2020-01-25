from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rest_framework_extensions.mixins import NestedViewSetMixin

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
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], url_path='users-list-action')
    def users_list_action(self, request, *args, **kwargs):
        return Response('users list action')

    @action(detail=True, methods=['post'], url_path='users-action')
    def users_action(self, request, *args, **kwargs):
        return Response('users action')


class GroupViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = GroupModel.objects.all()
    serializer_class = GroupSerializer

    @action(detail=False, url_path='groups-list-link')
    def groups_list_link(self, request, *args, **kwargs):
        return Response('groups list link')

    @action(detail=True, url_path='groups-link')
    def groups_link(self, request, *args, **kwargs):
        return Response('groups link')


class PermissionViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = PermissionModel.objects.all()
    serializer_class = PermissionSerializer

    @action(detail=False, methods=['post'], url_path='permissions-list-action')
    def permissions_list_action(self, request, *args, **kwargs):
        return Response('permissions list action')

    @action(detail=True, methods=['post'], url_path='permissions-action')
    def permissions_action(self, request, *args, **kwargs):
        return Response('permissions action')


class TaskViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = TaskModel.objects.all()
    serializer_class = TaskSerializer


class BookViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = BookModel.objects.all()
    serializer_class = BookSerializer


class CommentViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer


class TaskCommentViewSet(CommentViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(
            content_type=ContentType.objects.get_for_model(TaskModel)
        )


class BookCommentViewSet(CommentViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(
            content_type=ContentType.objects.get_for_model(BookModel)
        )


class UserViewSetWithEmailLookup(NestedViewSetMixin, ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'email'
    lookup_value_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
