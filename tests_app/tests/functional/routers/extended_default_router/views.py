from rest_framework.viewsets import ModelViewSet

from rest_framework_extensions.mixins import NestedViewSetMixin

from .models import (
    DefaultRouterUserModel,
    DefaultRouterGroupModel,
    DefaultRouterPermissionModel,
)


class UserViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = DefaultRouterUserModel.objects.all()


class GroupViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = DefaultRouterGroupModel.objects.all()


class PermissionViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = DefaultRouterPermissionModel.objects.all()
