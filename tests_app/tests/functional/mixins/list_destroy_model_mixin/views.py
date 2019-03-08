import django_filters
from rest_framework import viewsets, serializers
from rest_framework import filters
from rest_framework.permissions import DjangoModelPermissions
from rest_framework_extensions.bulk_operations.mixins import ListDestroyModelMixin

from .models import CommentForListDestroyModelMixin as Comment


class CommentFilter(django_filters.FilterSet):
    class Meta:
        model = Comment
        fields = [
            'id'
        ]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class CommentViewSet(ListDestroyModelMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = CommentFilter


class CommentViewSetWithPermissions(CommentViewSet):
    permission_classes = (DjangoModelPermissions,)
