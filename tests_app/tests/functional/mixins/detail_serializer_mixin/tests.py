import datetime

from django.test import TestCase, override_settings

# todo: use from rest_framework when released
from rest_framework.test import APIRequestFactory
from .models import Comment


factory = APIRequestFactory()


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.detail_serializer_mixin.urls')
class DetailSerializerMixinTest_serializer_detail_class(TestCase):

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
        self.assertEqual(resp.data, expected)

    def test_serializer_detail_class_response(self):
        resp = self.client.get('/comments/1/')
        expected = {
            'id': 1,
            'email': 'example@ya.ru',
            'content': 'Hello world',
        }
        self.assertEqual(resp.data, expected, 'should use detail serializer for detail endpoint')

    def test_view_with_mixin_and_without__serializer_detail_class__should_raise_exception(self):
        msg = "'CommentWithoutDetailSerializerClassViewSet' should include a 'serializer_detail_class' attribute"
        self.assertRaisesMessage(AssertionError, msg, self.client.get, '/comments-2/')


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.detail_serializer_mixin.urls')
class DetailSerializerMixin_queryset_detail(TestCase):

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
        self.assertEqual(resp.data, expected)

    def test_detail_view_should_use_default_queryset_if_queryset_detail_not_specified(self):
        resp = self.client.get('/comments-3/1/')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/comments-3/2/')
        expected = {
            'id': 2,
            'email': 'example2@ya.ru',
            'content': 'Hello world 2',
        }
        self.assertEqual(resp.data, expected)

    def test_list_should_use_default_queryset_method_if_queryset_detail_specified(self):
        resp = self.client.get('/comments-4/')
        expected = [{
            'id': 2,
            'email': 'example2@ya.ru'
        }]
        self.assertEqual(resp.data, expected)

    def test_detail_view_should_use_custom_queryset_if_queryset_detail_specified(self):
        resp = self.client.get('/comments-4/2/')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/comments-4/1/')
        expected = {
            'id': 1,
            'email': 'example@ya.ru',
            'content': 'Hello world',
        }
        self.assertEqual(resp.data, expected)

    def test_nested_model_view_with_mixin_should_use_get_detail_queryset(self):
        """
        Regression tests for https://github.com/chibisov/drf-extensions/pull/24
        """
        resp = self.client.get('/comments-5/1/')
        expected = {
            'id': 1,
            'email': 'example@ya.ru',
            'content': 'Hello world',
        }
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, expected)
