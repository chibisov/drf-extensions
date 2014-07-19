# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework_extensions.mixins import DetailSerializerMixin, NestedViewSetMixin

from .models import Comment
from .serializers import CommentSerializer, CommentDetailSerializer


class CommentViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    serializer_detail_class = CommentDetailSerializer
    queryset = Comment.objects.all()


class CommentWithoutDetailSerializerClassViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()


class CommentWithIdTwoViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    serializer_detail_class = CommentDetailSerializer
    queryset = Comment.objects.filter(id=2)


class CommentWithIdTwoAndIdOneForDetailViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    serializer_detail_class = CommentDetailSerializer
    queryset = Comment.objects.filter(id=2)
    queryset_detail = Comment.objects.filter(id=1)


class CommentNestedModelViewSet(NestedViewSetMixin, DetailSerializerMixin, viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    serializer_detail_class = CommentDetailSerializer
    queryset = Comment.objects.all()
    queryset_detail = Comment.objects.filter(id=1)

