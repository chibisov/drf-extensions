import datetime

from django.test import TestCase, override_settings

from .models import CommentForPaginateByMaxMixin


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.paginate_by_max_mixin.urls')
class PaginateByMaxMixinTest(TestCase):

    def setUp(self):
        for i in range(30):
            CommentForPaginateByMaxMixin.objects.create(
                email='example@ya.ru',
                content='Hello world',
                created=datetime.datetime.now()
            )

    def test_default_page_size(self):
        resp = self.client.get('/comments/')
        self.assertEqual(len(resp.data['results']), 10)

    def test_custom_page_size__less_then_maximum(self):
        resp = self.client.get('/comments/?limit=15')
        self.assertEqual(len(resp.data['results']), 15)

    def test_custom_page_size__more_then_maximum(self):
        resp = self.client.get('/comments/?limit=25')
        self.assertEqual(len(resp.data['results']), 20)

    def test_custom_page_size_with_max_value(self):
        resp = self.client.get('/comments/?limit=max')
        self.assertEqual(len(resp.data['results']), 20)

    def test_custom_page_size_with_max_value__for_view_without__paginate_by_param__attribute(self):
        resp = self.client.get(
            '/comments-without-paginate-by-param-attribute/?page_size=max')
        self.assertEqual(len(resp.data['results']), 10)

    def test_custom_page_size_with_max_value__for_view_without__max_paginate_by__attribute(self):
        resp = self.client.get(
            '/comments-without-max-paginate-by-attribute/?page_size=max')
        self.assertEqual(len(resp.data['results']), 10)


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.paginate_by_max_mixin.urls')
class PaginateByMaxMixinTestBehavior__should_not_affect_view_if_DRF_does_not_supports__max_paginate_by(TestCase):

    def setUp(self):
        for i in range(30):
            CommentForPaginateByMaxMixin.objects.create(
                email='example@ya.ru',
                content='Hello world',
                created=datetime.datetime.now()
            )

    def test_default_page_size(self):
        resp = self.client.get('/comments/')
        self.assertEqual(len(resp.data['results']), 10)

    def test_custom_page_size__less_then_maximum(self):
        resp = self.client.get('/comments/?limit=15')
        self.assertEqual(len(resp.data['results']), 15)

    def test_custom_page_size__more_then_maximum(self):
        resp = self.client.get('/comments/?limit=25')
        self.assertEqual(len(resp.data['results']), 20)

    def test_custom_page_size_with_max_value(self):
        resp = self.client.get('/comments/?limit=max')
        self.assertEqual(len(resp.data['results']), 20)
