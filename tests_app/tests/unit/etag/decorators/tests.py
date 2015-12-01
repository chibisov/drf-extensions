# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils.http import quote_etag

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS

from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.test import APIRequestFactory
from rest_framework_extensions.utils import prepare_header_name

from tests_app.testutils import (
    override_extensions_api_settings,
)


factory = APIRequestFactory()
UNSAFE_METHODS = ('POST', 'PUT', 'DELETE', 'PATCH')


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


class ETAGProcessorTestBehaviorMixin(object):
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
        super(ETAGProcessorTestBehavior_if_none_match, self).setUp()
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
        super(ETAGProcessorTestBehavior_if_match, self).setUp()
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
