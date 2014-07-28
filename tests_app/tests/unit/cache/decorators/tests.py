# -*- coding: utf-8 -*-
from mock import Mock, patch

from django.test import TestCase
from django.core.cache import cache, get_cache
from django.utils import unittest

from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.test import APIRequestFactory
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework_extensions.utils import get_django_features

from tests_app.testutils import override_extensions_api_settings


factory = APIRequestFactory()


class CacheResponseTest(TestCase):
    def setUp(self):
        super(CacheResponseTest, self).setUp()
        self.request = factory.get('')
        self.cache = get_cache(extensions_api_settings.DEFAULT_USE_CACHE)

    def test_should_return_response_if_it_is_not_in_cache(self):
        class TestView(views.APIView):
            @cache_response()
            def get(self, request, *args, **kwargs):
                return Response('Response from method 1')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertEqual(response.data, 'Response from method 1')
        self.assertEqual(type(response), Response)

    @override_extensions_api_settings(DEFAULT_CACHE_KEY_FUNC=Mock(return_value='cache_response_key'))
    def test_should_store_response_in_cache_by_key_function_which_specified_in_settings(self):
        class TestView(views.APIView):
            @cache_response()
            def get(self, request, *args, **kwargs):
                return Response('Response from method 2')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertEqual(cache.get('cache_response_key').content, response.content)
        self.assertEqual(type(response), Response)

    def test_should_store_response_in_cache_by_key_function_which_specified_in_arguments(self):
        def key_func(*args, **kwargs):
            return 'cache_response_key_from_func'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from method 3')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertEqual(cache.get('cache_response_key_from_func').content, response.content)
        self.assertEqual(type(response), Response)

    def test_should_store_response_in_cache_by_key_which_calculated_by_view_method__if__key_func__is_string(self):
        class TestView(views.APIView):
            @cache_response(key_func='key_func')
            def get(self, request, *args, **kwargs):
                return Response('Response from method 3')

            def key_func(self, *args, **kwargs):
                return 'cache_response_key_from_method'

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertEqual(cache.get('cache_response_key_from_method').content, response.content)
        self.assertEqual(type(response), Response)

    def test_key_func_call_arguments(self):
        called_with_kwargs = {}

        def key_func(**kwargs):
            called_with_kwargs.update(kwargs)
            return 'cache_response_key_from_func'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from method 3')

        view_instance = TestView()
        response = view_instance.dispatch(self.request, 'hello', hello='world')
        self.assertEqual(called_with_kwargs.get('view_instance'), view_instance)
        # self.assertEqual(called_with_kwargs.get('view_method'), view_instance.get)  # todo: test me
        self.assertEqual(called_with_kwargs.get('args'), ('hello',))
        self.assertEqual(called_with_kwargs.get('kwargs'), {'hello': 'world'})

    @override_extensions_api_settings(
        DEFAULT_CACHE_RESPONSE_TIMEOUT=100,
        DEFAULT_CACHE_KEY_FUNC=Mock(return_value='cache_response_key')
    )
    def test_should_store_response_in_cache_with_timeout_from_settings(self):
        cache_response_decorator = cache_response()
        cache_response_decorator.cache.set = Mock()

        class TestView(views.APIView):
            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(cache_response_decorator.cache.set.called, 'Cache saving should be performed')
        self.assertEqual(cache_response_decorator.cache.set.call_args_list[0][0][2], 100)

    def test_should_store_response_in_cache_with_timeout_from_arguments(self):
        cache_response_decorator = cache_response(timeout=3)
        cache_response_decorator.cache.set = Mock()

        class TestView(views.APIView):
            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(cache_response_decorator.cache.set.called, 'Cache saving should be performed')
        self.assertEqual(cache_response_decorator.cache.set.call_args_list[0][0][2], 3)

    def test_should_return_response_from_cache_if_it_is_in_it(self):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response(u'Response from method 4')

        view_instance = TestView()
        view_instance.headers = {}
        cached_response = Response(u'Cached response from method 4')
        view_instance.finalize_response(request=self.request, response=cached_response)
        cached_response.render()
        self.cache.set('cache_response_key', cached_response)

        response = view_instance.dispatch(request=self.request)
        self.assertEqual(response.content.decode('utf-8'), u'"Cached response from method 4"')

    @override_extensions_api_settings(
        DEFAULT_USE_CACHE='special_cache'
    )
    def test_should_use_cache_from_settings_by_default(self):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response(u'Response from method 5')

        view_instance = TestView()
        view_instance.dispatch(request=self.request)
        data_from_cache = get_cache('special_cache').get('cache_response_key')
        self.assertTrue(hasattr(data_from_cache, 'content'))
        self.assertEqual(data_from_cache.content.decode('utf-8'), u'"Response from method 5"')

    @override_extensions_api_settings(
        DEFAULT_USE_CACHE='special_cache'
    )
    def test_should_use_cache_from_decorator_if_it_is_specified(self):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func, cache='another_special_cache')
            def get(self, request, *args, **kwargs):
                return Response(u'Response from method 6')

        view_instance = TestView()
        view_instance.dispatch(request=self.request)
        data_from_cache = get_cache('another_special_cache').get('cache_response_key')
        self.assertTrue(hasattr(data_from_cache, 'content'))
        self.assertEqual(data_from_cache.content.decode('utf-8'), u'"Response from method 6"')

    @unittest.skipUnless(
        get_django_features()['caches_singleton'],
        "Current django version doesn't support caches singleton"
    )
    def test_should_reuse_cache_singleton(self):
        """
        https://github.com/chibisov/drf-extensions/issues/26
        https://docs.djangoproject.com/en/dev/topics/cache/#django.core.cache.caches
        """
        cache_response_instance = cache_response()
        another_cache_response_instance = cache_response()
        self.assertTrue(cache_response_instance.cache is another_cache_response_instance.cache)