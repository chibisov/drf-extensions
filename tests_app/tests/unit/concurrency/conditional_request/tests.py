from django.test import TestCase
from django.utils.http import quote_etag
from rest_framework import status
from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.decorators import precondition_required
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.exceptions import PreconditionRequiredException
from rest_framework_extensions.test import APIRequestFactory
from rest_framework_extensions.utils import prepare_header_name

factory = APIRequestFactory()
UNSAFE_METHODS = ('POST', 'PUT', 'DELETE', 'PATCH')


def default_api_etag_func(**kwargs):
    return 'hello'


class PreconditionRequiredTestCase(TestCase):
    def test_should_add_object_etag_value_empty_precondition_map_decorator(self):
        class TestView(views.APIView):
            @precondition_required(precondition_map={})
            @etag(default_api_etag_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from GET method')

        view_instance = TestView()
        response = view_instance.get(request=factory.get(''))
        expected_etag_value = default_api_etag_func()
        self.assertEqual(response.get('Etag'), quote_etag(expected_etag_value))
        self.assertEqual(response.data, 'Response from GET method')

    def test_should_require_precondition_decorator_unsafe_methods_default(self):
        class TestView(views.APIView):
            @precondition_required()
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required()
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required()
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

    def test_should_require_precondition_decorator_unsafe_methods_explicit(self):
        class TestView(views.APIView):
            @precondition_required(precondition_map={'PUT': ['If-Match']})
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required(precondition_map={'PATCH': ['If-Match']})
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required(precondition_map={'DELETE': ['If-Match']})
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

    def test_should_require_precondition_decorator_unsafe_methods_explicit_tuple(self):
        class TestView(views.APIView):
            @precondition_required(precondition_map={'PUT': ('If-Match',)})
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required(precondition_map={'PATCH': ('If-Match',)})
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required(precondition_map={'DELETE': ('If-Match',)})
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

    def test_should_require_precondition_decorator_unsafe_methods_explicit_set(self):
        class TestView(views.APIView):
            @precondition_required(precondition_map={'PUT': {'If-Match'}})
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required(precondition_map={'PATCH': {'If-Match'}})
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required(precondition_map={'DELETE': {'If-Match'}})
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete(''))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

    def test_should_not_require_preconditions_for_unsafe_methods(self):
        class TestView(views.APIView):
            @precondition_required({})
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required({})
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required({})
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        response = view_instance.put(request=factory.put(''))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PUT method')

        response = view_instance.patch(request=factory.patch(''))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PATCH method')

        response = view_instance.delete(request=factory.delete(''))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, 'Response from DELETE method')

    def test_should_not_require_preconditions_for_delete(self):
        class TestView(views.APIView):
            @precondition_required({})
            @etag(default_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required({})
            @etag(default_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required({'PUT': {}})
            @etag(default_api_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        view_instance = TestView()
        response = view_instance.put(request=factory.put(''))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PUT method')

        response = view_instance.patch(request=factory.patch(''))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PATCH method')

        response = view_instance.delete(request=factory.delete(''))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, 'Response from DELETE method')

    def test_precondition_decorator_unsafe_methods_if_none_match(self):
        def dummy_etag_func(**kwargs):
            return 'some_etag'

        class TestView(views.APIView):
            @precondition_required()
            @etag(dummy_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required()
            @etag(dummy_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required()
            @etag(dummy_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        headers = {
            prepare_header_name('if-none-match'): 'some_etag'
        }

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

    def test_precondition_decorator_unsafe_methods_if_match(self):
        def dummy_etag_func(**kwargs):
            return 'some_etag'

        class TestView(views.APIView):
            @precondition_required()
            @etag(dummy_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required()
            @etag(dummy_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required()
            @etag(dummy_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        headers = {
            prepare_header_name('if-match'): 'some_etag'
        }

        view_instance = TestView()
        response = view_instance.put(request=factory.put('', **headers))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PUT method')

        response = view_instance.patch(request=factory.patch('', **headers))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Response from PATCH method')

        response = view_instance.delete(request=factory.delete('', **headers))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, 'Response from DELETE method')

    def test_should_require_precondition_decorator_custom_headers(self):
        def dummy_etag_func(**kwargs):
            return 'some_etag'

        class TestView(views.APIView):
            @precondition_required({'PUT': ['X-custom-header']})
            @etag(dummy_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required({'PATCH': ['X-custom-header']})
            @etag(dummy_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required({'DELETE': ['X-custom-header']})
            @etag(dummy_etag_func)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        headers = {
            prepare_header_name('if-match'): 'some_etag'
        }

        view_instance = TestView()
        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.put(request=factory.put('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.patch(request=factory.patch('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)

        with self.assertRaises(PreconditionRequiredException) as cm:
            view_instance.delete(request=factory.delete('', **headers))
        self.assertEqual(cm.exception.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertIsNotNone(cm.exception.detail)
