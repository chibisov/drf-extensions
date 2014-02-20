# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework_extensions.mixins import PaginateByMaxMixin

from .models import CommentForPaginateByMaxMixin
from .serializers import CommentSerializer


class CommentViewSet(PaginateByMaxMixin, viewsets.ReadOnlyModelViewSet):
    paginate_by_param = 'page_size'
    paginate_by = 10
    max_paginate_by = 20
    serializer_class = CommentSerializer
    queryset = CommentForPaginateByMaxMixin.objects.all()


class CommentWithoutPaginateByParamViewSet(PaginateByMaxMixin, viewsets.ReadOnlyModelViewSet):
    paginate_by = 10
    max_paginate_by = 20
    serializer_class = CommentSerializer
    queryset = CommentForPaginateByMaxMixin.objects.all()


class CommentWithoutMaxPaginateByAttributeViewSet(PaginateByMaxMixin, viewsets.ReadOnlyModelViewSet):
    paginate_by_param = 'page_size'
    paginate_by = 10
    serializer_class = CommentSerializer
    queryset = CommentForPaginateByMaxMixin.objects.all()