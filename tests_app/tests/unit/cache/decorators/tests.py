from django.core.cache import caches
from django.test import TestCase
from mock import Mock, patch
from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework.test import APIRequestFactory
from tests_app.testutils import override_extensions_api_settings

factory = APIRequestFactory()


class CacheResponseTest(TestCase):
    def setUp(self):
        super().setUp()
        self.request = factory.get('')
        self.cache = caches[extensions_api_settings.DEFAULT_USE_CACHE]

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
        self.assertEqual(self.cache.get('cache_response_key')
                         [0], response.content)
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
        self.assertEqual(self.cache.get(
            'cache_response_key_from_func')[0], response.content)
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
        self.assertEqual(self.cache.get(
            'cache_response_key_from_method')[0], response.content)
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
        self.assertEqual(called_with_kwargs.get(
            'view_instance'), view_instance)
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
        self.assertTrue(
            cache_response_decorator.cache.set.called,
            'Cache saving should be performed')
        self.assertEqual(
            cache_response_decorator.cache.set.call_args_list[0][0][2], 100)

    def test_should_store_response_in_cache_with_timeout_from_arguments(self):
        cache_response_decorator = cache_response(timeout=3)
        cache_response_decorator.cache.set = Mock()

        class TestView(views.APIView):
            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(
            cache_response_decorator.cache.set.called,
            'Cache saving should be performed')
        self.assertEqual(
            cache_response_decorator.cache.set.call_args_list[0][0][2], 3)

    def test_should_store_response_in_cache_with_timeout_from_object_cache_timeout_property(self):
        cache_response_decorator = cache_response(
            timeout='object_cache_timeout')
        cache_response_decorator.cache.set = Mock()

        class TestView(views.APIView):
            object_cache_timeout = 20

            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(
            cache_response_decorator.cache.set.called,
            'Cache saving should be performed')
        self.assertEqual(
            cache_response_decorator.cache.set.call_args_list[0][0][2], 20)

    def test_should_store_response_in_cache_with_timeout_from_list_cache_timeout_property(self):
        cache_response_decorator = cache_response(timeout='list_cache_timeout')
        cache_response_decorator.cache.set = Mock()

        class TestView(views.APIView):
            list_cache_timeout = 10

            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response('Response from method 4')

        view_instance = TestView()
        response = view_instance.dispatch(request=self.request)
        self.assertTrue(
            cache_response_decorator.cache.set.called,
            'Cache saving should be performed')
        self.assertEqual(
            cache_response_decorator.cache.set.call_args_list[0][0][2], 10)

    def test_should_return_response_from_cache_if_it_is_in_it(self):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response(u'Response from method 4')

        view_instance = TestView()
        view_instance.headers = {}
        cached_response = Response('Cached response from method 4')
        view_instance.finalize_response(
            request=self.request, response=cached_response)
        cached_response.render()
        response_dict = (
            cached_response.rendered_content,
            cached_response.status_code,
            cached_response._headers
        )
        self.cache.set('cache_response_key', response_dict)

        response = view_instance.dispatch(request=self.request)
        self.assertEqual(
            response.content.decode('utf-8'),
            '"Cached response from method 4"')

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
        data_from_cache = caches['special_cache'].get('cache_response_key')
        self.assertEqual(len(data_from_cache), 3)
        self.assertEqual(
            data_from_cache[0].decode('utf-8'),
            u'"Response from method 5"')

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
        data_from_cache = caches['another_special_cache'].get(
            'cache_response_key')
        self.assertEqual(len(data_from_cache), 3)
        self.assertEqual(data_from_cache[0].decode(
            'utf-8'), u'"Response from method 6"')

    def test_should_reuse_cache_singleton(self):
        """
        https://github.com/chibisov/drf-extensions/issues/26
        https://docs.djangoproject.com/en/dev/topics/cache/#django.core.cache.caches
        """
        cache_response_instance = cache_response()
        another_cache_response_instance = cache_response()
        self.assertTrue(
            cache_response_instance.cache is another_cache_response_instance.cache)

    def test_dont_cache_response_with_error_if_cache_error_false(self):
        cache_response_decorator = cache_response(cache_errors=False)

        class TestView(views.APIView):

            def __init__(self, status, *args, **kwargs):
                self.status = status
                super().__init__(*args, **kwargs)

            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response(status=self.status)

        with patch.object(cache_response_decorator.cache, 'set'):
            for status in (400, 500):
                view_instance = TestView(status=status)
                view_instance.dispatch(request=self.request)

                self.assertFalse(cache_response_decorator.cache.set.called)

    def test_cache_response_with_error_by_default(self):
        cache_response_decorator = cache_response()

        class TestView(views.APIView):

            def __init__(self, status, *args, **kwargs):
                self.status = status
                super().__init__(*args, **kwargs)

            @cache_response_decorator
            def get(self, request, *args, **kwargs):
                return Response(status=self.status)

        with patch.object(cache_response_decorator.cache, 'set'):
            for status in (400, 500):
                view_instance = TestView(status=status)
                view_instance.dispatch(request=self.request)

                self.assertTrue(cache_response_decorator.cache.set.called)

    @override_extensions_api_settings(
        DEFAULT_CACHE_ERRORS=False
    )
    def test_should_use_cache_error_from_settings_by_default(self):
        self.assertFalse(cache_response().cache_errors)

    @override_extensions_api_settings(
        DEFAULT_CACHE_ERRORS=False
    )
    def test_should_use_cache_error_from_decorator_if_it_is_specified(self):
        self.assertTrue(cache_response(cache_errors=True).cache_errors)

    def test_should_return_response_with_tuple_headers(self):
        def key_func(**kwargs):
            return 'cache_response_key'

        class TestView(views.APIView):
            @cache_response(key_func=key_func)
            def get(self, request, *args, **kwargs):
                return Response(u'')

        view_instance = TestView()
        view_instance.headers = {'Test': 'foo'}
        cached_response = Response(u'')
        view_instance.finalize_response(
            request=self.request, response=cached_response)
        cached_response.render()
        response_dict = (
            cached_response.rendered_content,
            cached_response.status_code,
            {k: list(v) for k, v in cached_response._headers.items()}
        )
        self.cache.set('cache_response_key', response_dict)

        response = view_instance.dispatch(request=self.request)
        self.assertTrue(all(isinstance(v, tuple)
                            for v in response._headers.values()))
        self.assertEqual(response._headers['test'], ('Test', 'foo'))
