from django.test import TestCase
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework_extensions.utils import prepare_header_name

from rest_framework_extensions.decorators import precondition_required
from rest_framework_extensions.test import APIRequestFactory

factory = APIRequestFactory()


class PreconditionRequiredProcessorTest(TestCase):
    def test_default_function_call(self):
        decorator = precondition_required()
        self.assertIsNotNone(decorator.precondition_map)

    def test_default_decorator(self):
        class TestView(views.APIView):
            @precondition_required()
            def get(self, request, *args, **kwargs):
                return super(TestView, self).get(request, *args, **kwargs)

    def test_decorator_explicit(self):
        class TestView(views.APIView):
            @precondition_required(precondition_map={'PUT': ['If-Match']})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_decorator_explicit_positional(self):
        class TestView(views.APIView):
            @precondition_required({'PUT': ['If-Match']})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_decorator_empty(self):
        class TestView(views.APIView):
            @precondition_required({})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_decorator_method_empty_list(self):
        class TestView(views.APIView):
            @precondition_required({'PUT': []})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_decorator_method_empty_set(self):
        class TestView(views.APIView):
            @precondition_required({'PUT': {}})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_decorator_method_empty_tuple(self):
        class TestView(views.APIView):
            @precondition_required({'PUT': ()})
            def put(self, request, *args, **kwargs):
                return super(TestView, self).put(request, *args, **kwargs)

    def test_should_raise_assertion_error_if_precondition_map_not_a_dict(self):
        with self.assertRaises(AssertionError):
            precondition_required(precondition_map=['header-name'])

    def test_should_raise_assertion_error_if_precondition_map_not_a_dict_decorator(self):
        with self.assertRaises(AssertionError):
            class View(views.APIView):
                @precondition_required(precondition_map=['header-name'])
                def get(self, request, *args, **kwargs):
                    return super(View, self).get(request, *args, **kwargs)

    def test_precondition_decorator_custom_headers(self):
        class TestView(views.APIView):
            @precondition_required({'PUT': ['X-custom-header']})
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @precondition_required({'PATCH': ['X-custom-header']})
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @precondition_required({'DELETE': ['X-custom-header']})
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        headers = {
            prepare_header_name('X-custom-header'): 'some_value'
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
