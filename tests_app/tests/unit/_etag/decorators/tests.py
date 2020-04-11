from django.test import TestCase
from django.utils.http import quote_etag

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS
from rest_framework_extensions.exceptions import PreconditionRequiredException

from rest_framework_extensions.etag.decorators import (etag, api_etag)
from rest_framework.test import APIRequestFactory
from rest_framework_extensions.utils import prepare_header_name

from tests_app.testutils import (
    override_extensions_api_settings,
)

factory = APIRequestFactory()
UNSAFE_METHODS = ('POST', 'PUT', 'DELETE', 'PATCH')


def dummy_api_etag_func(**kwargs):
    return 'hello'


def default_etag_func(**kwargs):
    return 'hello'


@override_extensions_api_settings(DEFAULT_ETAG_FUNC=default_etag_func)
class ETAGProcessorTest(TestCase):
    def setUp(self):
        self.request = factory.get('')

    def test_should_use_etag_func_from_settings_if_it_is_not_specified(self):
        etag_decorator = etag()
        self.assertEqual(etag_decorator.etag_func, default_etag_func)

    def test_should_add_default_etag_value(self):
        class TestView(views.APIView):
            @etag()
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = default_etag_func()
        self.assertEqual(response.get('Etag'), quote_etag(expected_etag_value))
        self.assertEqual(response.data, 'Response from method')

    def test_should_not_change_existing_etag_value(self):
        class TestView(views.APIView):
            @etag()
            def get(self, request, *args, **kwargs):
                return Response('Response from method', headers={'etag': 'hello'})

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = 'hello'
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')

    def test_should_not_change_existing_etag_value__even_if_it_is_empty(self):
        class TestView(views.APIView):
            @etag()
            def get(self, request, *args, **kwargs):
                return Response('Response from method', headers={'etag': ''})

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = ''
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')

    def test_should_use_custom_func_if_it_is_defined(self):
        def calculate_etag(**kwargs):
            return 'Custom etag'

        class TestView(views.APIView):
            @etag(calculate_etag)
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = quote_etag('Custom etag')
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')

    def test_should_use_custom_method_from_view_if__etag_func__is_string(self):
        used_kwargs = {}

        class TestView(views.APIView):
            @etag('calculate_etag')
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

            def calculate_etag(self, **kwargs):
                used_kwargs.update(kwargs)
                used_kwargs.update({'self': self})
                return 'Custom etag'

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = quote_etag('Custom etag')
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')
        self.assertEqual(used_kwargs['self'], used_kwargs['view_instance'])

    def test_custom_func_arguments(self):
        called_with_kwargs = {}

        def calculate_etag(**kwargs):
            called_with_kwargs.update(kwargs)
            return 'Custom etag'

        class TestView(views.APIView):
            @etag(calculate_etag)
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        view_instance.get(self.request, 'hello', hello='world')
        self.assertEqual(called_with_kwargs.get('view_instance'), view_instance)
        # self.assertEqual(called_with_kwargs.get('view_method'), view_instance.get)  # todo: test me
        self.assertEqual(called_with_kwargs.get('args'), ('hello',))
        self.assertEqual(called_with_kwargs.get('kwargs'), {'hello': 'world'})


class ETAGProcessorTestBehavior_rebuild_after_method_evaluation(TestCase):
    def setUp(self):
        self.request = factory.get('')

    def test_should_not__rebuild_after_method_evaluation__by_default(self):
        call_stack = []

        def calculate_etag(**kwargs):
            call_stack.append(1)
            return ''.join([str(i) for i in call_stack])

        class TestView(views.APIView):
            @etag(calculate_etag)
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        response = view_instance.get(self.request)
        expected_etag_value = quote_etag('1')
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')

    def test_should__rebuild_after_method_evaluation__if_it_asked(self):
        call_stack = []

        def calculate_etag(**kwargs):
            call_stack.append(1)
            return ''.join([str(i) for i in call_stack])

        class TestView(views.APIView):
            @etag(calculate_etag, rebuild_after_method_evaluation=True)
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        response = view_instance.get(self.request)
        expected_etag_value = quote_etag('11')
        self.assertEqual(response.get('Etag'), expected_etag_value)
        self.assertEqual(response.data, 'Response from method')


class ETAGProcessorTestBehaviorMixin:
    def setUp(self):
        def calculate_etag(**kwargs):
            return '123'

        class TestView(views.APIView):
            @etag(calculate_etag)
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        self.view_instance = TestView()
        self.expected_etag_value = quote_etag(calculate_etag())

    def run_for_methods(self, methods, condition_failed_status):
        for method in methods:
            for exp in self.experiments:
                headers = {
                    prepare_header_name(self.header_name): exp['header_value']
                }
                request = getattr(factory, method.lower())('', **headers)
                response = self.view_instance.get(request)
                base_msg = (
                    'For "{method}" and {header_name} value {header_value} condition should'
                ).format(
                    method=method,
                    header_name=self.header_name,
                    header_value=exp['header_value'],
                )
                if exp['should_fail']:
                    msg = base_msg + (
                        ' fail and response must be returned with {condition_failed_status} status. '
                        'But it is {response_status}'
                    ).format(condition_failed_status=condition_failed_status, response_status=response.status_code)
                    self.assertEqual(response.status_code, condition_failed_status, msg=msg)
                    msg = base_msg + ' fail and response must be empty'
                    self.assertEqual(response.data, None, msg=msg)
                    msg = (
                        'If precondition failed, then Etag must always be added to response. But it is {0}'
                    ).format(response.get('Etag'))
                    self.assertEqual(response.get('Etag'), self.expected_etag_value, msg=msg)
                else:
                    msg = base_msg + (
                        ' not fail and response must be returned with 200 status. '
                        'But it is "{response_status}"'
                    ).format(response_status=response.status_code)
                    self.assertEqual(response.status_code, status.HTTP_200_OK, msg=msg)
                    msg = base_msg + 'not fail and response must be filled'
                    self.assertEqual(response.data, 'Response from method', msg=msg)
                    self.assertEqual(response.get('Etag'), self.expected_etag_value, msg=msg)


class ETAGProcessorTestBehavior_if_none_match(ETAGProcessorTestBehaviorMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.header_name = 'if-none-match'
        self.experiments = [
            {
                'header_value': '123',
                'should_fail': True
            },
            {
                'header_value': '"123"',
                'should_fail': True
            },
            {
                'header_value': '321',
                'should_fail': False
            },
            {
                'header_value': '"321"',
                'should_fail': False
            },
            {
                'header_value': '"1234"',
                'should_fail': False
            },
            {
                'header_value': '"321" "123"',
                'should_fail': True
            },
            {
                'header_value': '321 "123"',
                'should_fail': True
            },
            {
                'header_value': '*',
                'should_fail': True
            },
            {
                'header_value': '"*"',
                'should_fail': True
            },
            {
                'header_value': '321 "*"',
                'should_fail': True
            },
        ]

    def test_for_safe_methods(self):
        self.run_for_methods(SAFE_METHODS, condition_failed_status=status.HTTP_304_NOT_MODIFIED)

    def test_for_unsafe_methods(self):
        self.run_for_methods(UNSAFE_METHODS, condition_failed_status=status.HTTP_412_PRECONDITION_FAILED)


class ETAGProcessorTestBehavior_if_match(ETAGProcessorTestBehaviorMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.header_name = 'if-match'
        self.experiments = [
            {
                'header_value': '123',
                'should_fail': False
            },
            {
                'header_value': '"123"',
                'should_fail': False
            },
            {
                'header_value': '321',
                'should_fail': True
            },
            {
                'header_value': '"321"',
                'should_fail': True
            },
            {
                'header_value': '"1234"',
                'should_fail': True
            },
            {
                'header_value': '"321" "123"',
                'should_fail': False
            },
            {
                'header_value': '321 "123"',
                'should_fail': False
            },
            {
                'header_value': '*',
                'should_fail': False
            },
            {
                'header_value': '"*"',
                'should_fail': False
            },
            {
                'header_value': '321 "*"',
                'should_fail': False
            },
        ]

    def test_for_all_methods(self):
        self.run_for_methods(
            tuple(SAFE_METHODS) + UNSAFE_METHODS,
            condition_failed_status=status.HTTP_412_PRECONDITION_FAILED
        )


class APIETAGProcessorTest(TestCase):
    """Unit test cases for the APIETAGProcessor and decorator functionality."""

    def setUp(self):
        self.request = factory.get('')

    def test_should_raise_assertion_error_if_etag_func_not_specified(self):
        with self.assertRaises(AssertionError):
            api_etag()

    def test_should_raise_assertion_error_if_etag_func_not_specified_decorator(self):
        with self.assertRaises(AssertionError):
            class View(views.APIView):
                @api_etag()
                def get(self, request, *args, **kwargs):
                    return super().get(request, *args, **kwargs)

    def test_should_raise_assertion_error_if_precondition_map_not_a_dict(self):
        with self.assertRaises(AssertionError):
            api_etag(etag_func=dummy_api_etag_func, precondition_map=['header-name'])

    def test_should_raise_assertion_error_if_precondition_map_not_a_dict_decorator(self):
        with self.assertRaises(AssertionError):
            class View(views.APIView):
                @api_etag(dummy_api_etag_func, precondition_map=['header-name'])
                def get(self, request, *args, **kwargs):
                    return super().get(request, *args, **kwargs)

    def test_should_add_object_etag_value(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from GET method')

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = dummy_api_etag_func()
        self.assertEqual(response.get('Etag'), quote_etag(expected_etag_value))
        self.assertEqual(response.data, 'Response from GET method')

    def test_should_add_object_etag_value_empty_precondition_map_decorator(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func, precondition_map={})
            def get(self, request, *args, **kwargs):
                return Response('Response from GET method')

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = dummy_api_etag_func()
        self.assertEqual(response.get('Etag'), quote_etag(expected_etag_value))
        self.assertEqual(response.data, 'Response from GET method')

    def test_should_add_object_etag_value_default_precondition_map_decorator(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func)
            def get(self, request, *args, **kwargs):
                return Response('Response from GET method')

        view_instance = TestView()
        response = view_instance.get(request=self.request)
        expected_etag_value = dummy_api_etag_func()
        self.assertEqual(response.get('Etag'), quote_etag(expected_etag_value))
        self.assertEqual(response.data, 'Response from GET method')


    def test_should_require_precondition_decorator_unsafe_methods_empty(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func, precondition_map={})
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @api_etag(dummy_api_etag_func, precondition_map={})
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @api_etag(dummy_api_etag_func, precondition_map={})
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

    def test_should_require_precondition_decorator_unsafe_methods_explicit(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func, precondition_map={'PUT': ['If-Match']})
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @api_etag(dummy_api_etag_func, precondition_map={'PATCH': ['If-Match']})
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @api_etag(dummy_api_etag_func, precondition_map={'DELETE': ['If-Match']})
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

    def test_precondition_decorator_unsafe_methods_if_none_match(self):
        def dummy_etag_func(**kwargs):
            return 'some_etag'

        class TestView(views.APIView):
            @api_etag(dummy_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @api_etag(dummy_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @api_etag(dummy_etag_func)
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

    def test_should_require_precondition_decorator_unsafe_methods_default(self):
        class TestView(views.APIView):
            @api_etag(dummy_api_etag_func)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @api_etag(dummy_api_etag_func)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @api_etag(dummy_api_etag_func)
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


class APIETAGProcessorTestBehaviorMixin:
    def setUp(self):
        def calculate_etag(**kwargs):
            return '123'

        class TestView(views.APIView):
            @api_etag(calculate_etag)
            def head(self, request, *args, **kwargs):
                return Response('Response from HEAD method')

            @api_etag(calculate_etag)
            def options(self, request, *args, **kwargs):
                return Response('Response from OPTIONS method')

            @api_etag(calculate_etag, precondition_map={})
            def post(self, request, *args, **kwargs):
                return Response('Response from POST method',
                                status=status.HTTP_201_CREATED)

            @api_etag(calculate_etag)
            def get(self, request, *args, **kwargs):
                return Response('Response from GET method')

            @api_etag(calculate_etag)
            def put(self, request, *args, **kwargs):
                return Response('Response from PUT method')

            @api_etag(calculate_etag)
            def patch(self, request, *args, **kwargs):
                return Response('Response from PATCH method')

            @api_etag(calculate_etag)
            def delete(self, request, *args, **kwargs):
                return Response('Response from DELETE method',
                                status=status.HTTP_204_NO_CONTENT)

        self.view_instance = TestView()
        self.expected_etag_value = quote_etag(calculate_etag())

    def run_for_methods(self, methods, condition_failed_status, experiments=None):
        for method in methods:
            if experiments is None:
                experiments = self.experiments
            for exp in experiments:
                headers = {
                    prepare_header_name(self.header_name): exp['header_value']
                }
                request = getattr(factory, method.lower())('', **headers)
                response = getattr(self.view_instance, method.lower())(request)
                base_msg = (
                    'For "{method}" and {header_name} value {header_value} condition should'
                ).format(
                    method=method,
                    header_name=self.header_name,
                    header_value=exp['header_value'],
                )
                if exp['should_fail']:
                    msg = base_msg + (
                        ' fail and response must be returned with {condition_failed_status} status. '
                        'But it is {response_status}'
                    ).format(condition_failed_status=condition_failed_status, response_status=response.status_code)
                    self.assertEqual(response.status_code, condition_failed_status, msg=msg)
                    msg = base_msg + ' fail and response must be empty'
                    self.assertEqual(response.data, None, msg=msg)
                    msg = (
                        'If precondition failed, then Etag must always be added to response. But it is {0}'
                    ).format(response.get('Etag'))
                    self.assertEqual(response.get('Etag'), self.expected_etag_value, msg=msg)
                else:
                    if method.lower() == 'delete':
                        success_status = status.HTTP_204_NO_CONTENT
                    elif method.lower() == 'post':
                        success_status = status.HTTP_201_CREATED
                    else:
                        success_status = status.HTTP_200_OK
                    msg = base_msg + (
                        ' not fail and response must be returned with %s status. '
                        'But it is "{response_status}"'
                    ).format(success_status, response_status=response.status_code)
                    self.assertEqual(response.status_code, success_status, msg=msg)
                    msg = base_msg + 'not fail and response must be filled'
                    self.assertEqual(response.data, 'Response from %s method' % method.upper(), msg=msg)
                    self.assertEqual(response.get('Etag'), self.expected_etag_value, msg=msg)


class APIETAGProcessorTestBehavior_if_match(APIETAGProcessorTestBehaviorMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.header_name = 'if-match'
        self.experiments = [
            {
                'header_value': '123',
                'should_fail': False
            },
            {
                'header_value': '"123"',
                'should_fail': False
            },
            {
                'header_value': '321',
                'should_fail': True
            },
            {
                'header_value': '"321"',
                'should_fail': True
            },
            {
                'header_value': '"1234"',
                'should_fail': True
            },
            {
                'header_value': '"321" "123"',
                'should_fail': False
            },
            {
                'header_value': '321 "123"',
                'should_fail': False
            },
            {
                'header_value': '*',
                'should_fail': False
            },
            {
                'header_value': '"*"',
                'should_fail': False
            },
            {
                'header_value': '321 "*"',
                'should_fail': False
            },
        ]

    def test_for_all_methods(self):
        self.run_for_methods(
            tuple(SAFE_METHODS) + UNSAFE_METHODS,
            condition_failed_status=status.HTTP_412_PRECONDITION_FAILED
        )


class APIETAGProcessorTestBehavior_if_none_match(APIETAGProcessorTestBehaviorMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.header_name = 'if-none-match'
        self.experiments = [
            {
                'header_value': '123',
                'should_fail': True
            },
            {
                'header_value': '"123"',
                'should_fail': True
            },
            {
                'header_value': '321',
                'should_fail': False
            },
            {
                'header_value': '"321"',
                'should_fail': False
            },
            {
                'header_value': '"1234"',
                'should_fail': False
            },
            {
                'header_value': '"321" "123"',
                'should_fail': True
            },
            {
                'header_value': '321 "123"',
                'should_fail': True
            },
            {
                'header_value': '*',
                'should_fail': True
            },
            {
                'header_value': '"*"',
                'should_fail': True
            },
            {
                'header_value': '321 "*"',
                'should_fail': True
            },
        ]

    def test_for_safe_methods(self):
        self.run_for_methods(SAFE_METHODS, condition_failed_status=status.HTTP_304_NOT_MODIFIED)

    # NB: We don't test the unsafe methods here, since the PreconditionRequiredException would require us to hack the
    # runner method. However, we tested the exceptions in the APIETAGProcessorTest class.
