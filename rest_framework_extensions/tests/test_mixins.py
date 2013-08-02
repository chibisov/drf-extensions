# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase

from rest_framework import serializers, routers
from rest_framework import viewsets

from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_extensions.tests.models import Comment
from rest_framework_extensions.test import APIRequestFactory  # todo: use from rest_framework when released


factory = APIRequestFactory()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'id',
            'email',
        )


class CommentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'id',
            'email',
            'content',
        )


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


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet)
viewset_router.register('comments-2', CommentWithoutDetailSerializerClassViewSet)
viewset_router.register('comments-3', CommentWithIdTwoViewSet)
viewset_router.register('comments-4', CommentWithIdTwoAndIdOneForDetailViewSet)
urlpatterns = viewset_router.urls


class TestDetailSerializerMixin(TestCase):
    urls = 'rest_framework_extensions.tests.test_mixins'

    def setUp(self):
        self.comment = Comment.objects.create(
            id=1,
            email='example@ya.ru',
            content='Hello world',
            created=datetime.datetime.now()
        )

    def test_serializer_class_response(self):
        resp = self.client.get('/comments/')
        expected = [{
            'id': 1,
            'email': 'example@ya.ru'
        }]
        self.assertEquals(resp.data, expected)

    def test_serializer_detail_class_response(self):
        resp = self.client.get('/comments/1/')
        expected = {
            'id': 1,
            'email': 'example@ya.ru',
            'content': 'Hello world',
        }
        self.assertEquals(resp.data, expected)

    def test_view_with_mixin_and_withou__serializer_detail_class__should_raise_exception(self):
        msg = "'CommentWithoutDetailSerializerClassViewSet' should include a 'serializer_detail_class' attribute"
        self.assertRaisesMessage(AssertionError, msg, self.client.get, '/comments-2/')


class TestDetailSerializerMixinQuerysetDetail(TestCase):
    urls = 'rest_framework_extensions.tests.test_mixins'

    def setUp(self):
        self.comments = [
            Comment.objects.create(
                id=1,
                email='example@ya.ru',
                content='Hello world',
                created=datetime.datetime.now()
            ),
            Comment.objects.create(
                id=2,
                email='example2@ya.ru',
                content='Hello world 2',
                created=datetime.datetime.now()
            ),
        ]

    def test_list_should_use_default_queryset_method(self):
        resp = self.client.get('/comments-3/')
        expected = [{
            'id': 2,
            'email': 'example2@ya.ru'
        }]
        self.assertEquals(resp.data, expected)

    def test_detail_view_should_use_default_queryset_if_queryset_detail_not_specified(self):
        resp = self.client.get('/comments-3/1/')
        self.assertEquals(resp.status_code, 404)

        resp = self.client.get('/comments-3/2/')
        expected = {
            'id': 2,
            'email': 'example2@ya.ru',
            'content': 'Hello world 2',
        }
        self.assertEquals(resp.data, expected)

    def test_list_should_use_default_queryset_method_if_queryset_detail_specified(self):
        resp = self.client.get('/comments-4/')
        expected = [{
            'id': 2,
            'email': 'example2@ya.ru'
        }]
        self.assertEquals(resp.data, expected)

    def test_detail_view_should_use_custom_queryset_if_queryset_detail_specified(self):
        resp = self.client.get('/comments-4/2/')
        self.assertEquals(resp.status_code, 404)

        resp = self.client.get('/comments-4/1/')
        expected = {
            'id': 1,
            'email': 'example@ya.ru',
            'content': 'Hello world',
        }
        self.assertEquals(resp.data, expected)
