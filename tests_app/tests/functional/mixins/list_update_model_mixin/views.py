import django_filters
from rest_framework import viewsets
from rest_framework import filters
from rest_framework.permissions import DjangoModelPermissions
from rest_framework_extensions.mixins import ListUpdateModelMixin

from .models import (
    CommentForListUpdateModelMixin as Comment,
    UserForListUpdateModelMixin as User
)
from .serializers import UserSerializer, CommentSerializer


class CommentFilter(django_filters.FilterSet):
    class Meta:
        model = Comment
        fields = [
            'id'
        ]


class CommentViewSet(ListUpdateModelMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = CommentFilter


class CommentViewSetWithPermissions(CommentViewSet):
    permission_classes = (DjangoModelPermissions,)


class UserViewSet(ListUpdateModelMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer