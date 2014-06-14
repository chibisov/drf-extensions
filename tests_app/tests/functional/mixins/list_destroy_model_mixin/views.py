# -*- coding: utf-8 -*-
import django_filters
from rest_framework import viewsets
from rest_framework import filters
from rest_framework.permissions import DjangoModelPermissions
from rest_framework_extensions.mixins import ListDestroyModelMixin

from .models import CommentForListDestroyModelMixin as Comment


class CommentFilter(django_filters.FilterSet):
    class Meta:
        model = Comment
        fields = [
            'id'
        ]


class CommentViewSet(ListDestroyModelMixin, viewsets.ModelViewSet):
    model = Comment
    queryset = Comment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CommentFilter


class CommentViewSetWithPermissions(CommentViewSet):
    permission_classes = (DjangoModelPermissions,)