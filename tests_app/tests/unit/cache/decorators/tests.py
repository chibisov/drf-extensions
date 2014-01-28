# -*- coding: utf-8 -*-
from mock import Mock, patch

from django.test import TestCase
from django.core.cache import cache

from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.test import APIRequestFactory
from rest_framework_extensions.cache.decorators import cache_response

from tests_app.testutils import override_extensions_api_settings


factory = APIRequestFactory()


class CacheResponseTest(TestCase):
    def setUp(self):
        super(CacheResponseTest, self).setUp()
        self.request = factory.get('')

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
    @patch('django.core.cache.cache.set')
    def test_should_store_response_in_cache_with_timeout_from_settings(self, cache_mock):
        class TestView(views.APIView):
            @cache_response()
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(cache_mock.called, 'Cache saving should be performed')
        self.assertEqual(cache_mock.call_args_list[0][0][2], 100)

    @patch('django.core.cache.cache.set')
    def test_should_store_response_in_cache_with_timeout_from_arguments(self, cache_mock):
        class TestView(views.APIView):
            @cache_response(timeout=3)
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(cache_mock.called, 'Cache saving should be performed')
        self.assertEqual(cache_mock.call_args_list[0][0][2], 3)

    @patch('django.core.cache.cache.set')
    def test_should_return_response_from_cache_if_it_is_in_it(self, cache_mock):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(cache_mock.called, 'Cache saving should be performed')
        self.assertEqual(cache_mock.call_args_list[0][0][0], 'cache_response_key')