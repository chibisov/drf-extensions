from mock import Mock
from mock import PropertyMock

import django
from django.test import TestCase
from django.utils.translation import override

from rest_framework import views
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from rest_framework_extensions.key_constructor.bits import (
    KeyBitDictBase,
    UniqueMethodIdKeyBit,
    LanguageKeyBit,
    FormatKeyBit,
    UserKeyBit,
    HeadersKeyBit,
    RequestMetaKeyBit,
    QueryParamsKeyBit,
    UniqueViewIdKeyBit,
    PaginationKeyBit,
    ListSqlQueryKeyBit,
    RetrieveSqlQueryKeyBit,
    ListModelKeyBit,
    RetrieveModelKeyBit,
    ArgsKeyBit,
    KwargsKeyBit,
)

from .models import BitTestModel


factory = APIRequestFactory()


class KeyBitDictBaseTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': [],
            'view_instance': None,
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }

    def test_should_raise_exception_if__get_source_dict__is_not_implemented(self):
        class KeyBitDictChild(KeyBitDictBase):
            pass

        try:
            KeyBitDictChild().get_data(**self.kwargs)
        except NotImplementedError:
            pass
        else:
            self.fail('Should raise NotImplementedError if "get_source_dict" method is not implemented')

    def test_should_return_empty_dict_if_source_dict_is_empty(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {}

        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), {})

    def test_should_retrieve_data_by_keys_from_params_list_from_source_dict(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'geobase_id': 123,
                    'name': 'London',
                }

        self.kwargs['params'] = ['name', 'geobase_id']
        expected = {
            'name': u'London',
            'geobase_id': u'123',
        }
        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), expected)

    def test_should_not_retrieve_data_with_none_value(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'geobase_id': 123,
                    'name': None,
                }

        self.kwargs['params'] = ['name', 'geobase_id']
        expected = {
            'geobase_id': u'123',
        }
        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), expected)

    def test_should_force_text_for_value(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'geobase_id': 123,
                    'name': 'Лондон',
                }

        self.kwargs['params'] = ['name', 'geobase_id']
        expected = {
            'geobase_id': u'123',
            'name': u'Лондон',
        }
        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), expected)

    def test_should_prepare_key_before_retrieving(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'GEOBASE_ID': 123,
                    'NAME': 'London',
                }

            def prepare_key_for_value_retrieving(self, key):
                return key.upper()

        self.kwargs['params'] = ['name', 'geobase_id']
        expected = {
            'geobase_id': u'123',
            'name': u'London',
        }
        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), expected)

    def test_should_prepare_key_before_value_assignment(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'geobase_id': 123,
                    'name': 'London',
                }

            def prepare_key_for_value_assignment(self, key):
                return key.upper()

        self.kwargs['params'] = ['name', 'geobase_id']
        expected = {
            'GEOBASE_ID': u'123',
            'NAME': u'London',
        }
        self.assertEqual(KeyBitDictChild().get_data(**self.kwargs), expected)

    def test_should_produce_exact_results_for_equal_params_attribute_with_different_items_ordering(self):
        class KeyBitDictChild(KeyBitDictBase):
            def get_source_dict(self, **kwargs):
                return {
                    'id': 1,
                    'GEOBASE_ID': 123,
                    'NAME': 'London',
                }

        self.kwargs['params'] = ['name', 'geobase_id']
        response_1 = KeyBitDictChild().get_data(**self.kwargs)
        self.kwargs['params'] = ['geobase_id', 'name']
        response_2 = KeyBitDictChild().get_data(**self.kwargs)
        self.assertEqual(response_1, response_2)


class UniqueViewIdKeyBitTest(TestCase):
    def test_resulting_dict(self):
        class TestView(views.APIView):
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        kwargs = {
            'params': None,
            'view_instance': view_instance,
            'view_method': view_instance.get,
            'request': None,
            'args': None,
            'kwargs': None
        }
        expected = u'tests_app.tests.unit.key_constructor.bits.tests' + u'.' + u'TestView'
        self.assertEqual(UniqueViewIdKeyBit().get_data(**kwargs), expected)


class UniqueMethodIdKeyBitTest(TestCase):
    def test_resulting_dict(self):
        class TestView(views.APIView):
            def get(self, request, *args, **kwargs):
                return Response('Response from method')

        view_instance = TestView()
        kwargs = {
            'params': None,
            'view_instance': view_instance,
            'view_method': view_instance.get,
            'request': None,
            'args': None,
            'kwargs': None
        }
        expected = u'tests_app.tests.unit.key_constructor.bits.tests' + u'.' + u'TestView' + u'.' + u'get'
        self.assertEqual(UniqueMethodIdKeyBit().get_data(**kwargs), expected)


class LanguageKeyBitTest(TestCase):
    def test_resulting_dict(self):
        kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }
        expected = u'br'

        with override('br'):
            self.assertEqual(LanguageKeyBit().get_data(**kwargs), expected)


class FormatKeyBitTest(TestCase):
    def test_resulting_dict(self):
        kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': factory.get(''),
            'args': None,
            'kwargs': None
        }
        kwargs['request'].accepted_renderer = Mock(format='super-format')
        expected = u'super-format'
        self.assertEqual(FormatKeyBit().get_data(**kwargs), expected)


class UserKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': factory.get(''),
            'args': None,
            'kwargs': None
        }
        self.user = Mock()
        self.user.id = 123
        self.is_authenticated = PropertyMock(return_value=False)
        type(self.user).is_authenticated = self.is_authenticated

    def test_without_user_in_request(self):
        expected = u'anonymous'
        self.assertEqual(UserKeyBit().get_data(**self.kwargs), expected)

    def test_with_not_autenticated_user(self):
        self.kwargs['request'].user = self.user
        expected = u'anonymous'
        self.assertEqual(UserKeyBit().get_data(**self.kwargs), expected)

    def test_with_autenticated_user(self):
        self.kwargs['request'].user = self.user
        self.is_authenticated.return_value = True
        expected = u'123'
        self.assertEqual(UserKeyBit().get_data(**self.kwargs), expected)


class HeadersKeyBitTest(TestCase):
    def test_resulting_dict(self):
        self.kwargs = {
            'params': ['Accept-Language', 'X-Geobase-Id', 'Not-Existing-Header'],
            'view_instance': None,
            'view_method': None,
            'request': factory.get('', **{
                'HTTP_ACCEPT_LANGUAGE': 'Ru',
                'HTTP_X_GEOBASE_ID': 123
            }),
            'args': None,
            'kwargs': None
        }
        expected = {
            'accept-language': u'Ru',
            'x-geobase-id': u'123'
        }
        self.assertEqual(HeadersKeyBit().get_data(**self.kwargs), expected)


class RequestMetaKeyBitTest(TestCase):
    def test_resulting_dict(self):
        self.kwargs = {
            'params': ['REMOTE_ADDR', 'REMOTE_HOST', 'not_existing_key'],
            'view_instance': None,
            'view_method': None,
            'request': factory.get('', **{
                'REMOTE_ADDR': '127.0.0.1',
                'REMOTE_HOST': 'localhost'
            }),
            'args': None,
            'kwargs': None
        }
        expected = {
            'REMOTE_ADDR': u'127.0.0.1',
            'REMOTE_HOST': u'localhost'
        }
        self.assertEqual(RequestMetaKeyBit().get_data(**self.kwargs), expected)


class QueryParamsKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': factory.get('?part=Londo&callback=jquery_callback'),
            'args': None,
            'kwargs': None
        }

    def test_resulting_dict(self):
        self.kwargs['params'] = ['part', 'callback', 'not_existing_param']
        expected = {
            'part': u'Londo',
            'callback': u'jquery_callback'
        }
        self.assertEqual(QueryParamsKeyBit().get_data(**self.kwargs), expected)

    def test_resulting_dict_all_params(self):
        self.kwargs['params'] = '*'
        expected = {
            'part': u'Londo',
            'callback': u'jquery_callback'
        }
        self.assertEqual(QueryParamsKeyBit().get_data(**self.kwargs), expected)

    def test_default_params_is_all_args(self):
        self.assertEqual(QueryParamsKeyBit().params, '*')


class PaginationKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': Mock(spec_set=['paginator']),
            'view_method': None,
            'request': factory.get('?page_size=10&page=1&limit=5&offset=15&cursor=foo'),
            'args': None,
            'kwargs': None
        }

    def test_view_without_pagination_arguments(self):
        self.kwargs['view_instance'] = Mock(spec_set=[])
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {})

    def test_view_with_empty_pagination_arguments(self):
        self.kwargs['view_instance'].paginator.page_query_param = None
        self.kwargs['view_instance'].paginator.page_size_query_param = None
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {})

    def test_view_with_page_kwarg(self):
        self.kwargs['view_instance'].paginator.page_query_param = 'page'
        self.kwargs['view_instance'].paginator.page_size_query_param = None
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {'page': '1'})

    def test_view_with_paginate_by_param(self):
        self.kwargs['view_instance'].paginator.page_query_param = None
        self.kwargs['view_instance'].paginator.page_size_query_param = 'page_size'
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {'page_size': '10'})

    def test_view_with_all_pagination_attrs(self):
        self.kwargs['view_instance'].paginator.page_query_param = 'page'
        self.kwargs['view_instance'].paginator.page_size_query_param = 'page_size'
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {'page_size': '10', 'page': '1'})

    def test_view_with_all_pagination_attrs__without_query_params(self):
        self.kwargs['view_instance'].paginator.page_query_param = 'page'
        self.kwargs['view_instance'].paginator.page_size_query_param = 'page_size'
        self.kwargs['request'] = factory.get('')
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {})

    def test_view_with_offset_pagination_attrs(self):
        self.kwargs['view_instance'].paginator.limit_query_param = 'limit'
        self.kwargs['view_instance'].paginator.offset_query_param = 'offset'
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {'limit': '5', 'offset': '15'})

    def test_view_with_cursor_pagination_attrs(self):
        self.kwargs['view_instance'].paginator.cursor_query_param = 'cursor'
        self.assertEqual(PaginationKeyBit().get_data(**self.kwargs), {'cursor': 'foo'})


class ListSqlQueryKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': Mock(),
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }
        self.kwargs['view_instance'].get_queryset = Mock(return_value=BitTestModel.objects.all())
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(is_active=True)

    def test_should_use_view__get_queryset__and_filter_it_with__filter_queryset(self):
        if django.VERSION >= (3, 1):
            expected = ('SELECT "unit_bittestmodel"."id", "unit_bittestmodel"."is_active" '
                        'FROM "unit_bittestmodel" '
                        'WHERE "unit_bittestmodel"."is_active"')
        else:
            expected = ('SELECT "unit_bittestmodel"."id", "unit_bittestmodel"."is_active" '
                        'FROM "unit_bittestmodel" '
                        'WHERE "unit_bittestmodel"."is_active" = True')

        response = ListSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, expected)

    def test_should_return_none_if_empty_queryset(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.none()
        response = ListSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_result_set_raised(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(pk__in=[])
        response = ListSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)


class ListModelKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': Mock(),
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }
        self.kwargs['view_instance'].get_queryset = Mock(return_value=BitTestModel.objects.all())
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(is_active=True)

    def test_should_use_view__get_queryset__and_filter_it_with__filter_queryset(self):
        # create 4 models
        BitTestModel.objects.create(is_active=True)
        BitTestModel.objects.create(is_active=True)
        BitTestModel.objects.create(is_active=True)
        BitTestModel.objects.create(is_active=True)

        expected = u"[(1, True), (2, True), (3, True), (4, True)]"

        response = ListModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, expected)

    def test_should_return_none_if_empty_queryset(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.none()
        response = ListModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_result_set_raised(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(pk__in=[])
        response = ListModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)


class RetrieveSqlQueryKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': Mock(),
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }
        self.kwargs['view_instance'].kwargs = {'id': 123}
        self.kwargs['view_instance'].lookup_field = 'id'
        self.kwargs['view_instance'].get_queryset = Mock(return_value=BitTestModel.objects.all())
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(is_active=True)

    def test_should_use_view__get_queryset__and_filter_it_with__filter_queryset__and_filter_by__lookup_field(self):
        if django.VERSION >= (3, 1):
            expected = ('SELECT "unit_bittestmodel"."id", "unit_bittestmodel"."is_active" '
                        'FROM "unit_bittestmodel" '
                        'WHERE ("unit_bittestmodel"."is_active" AND "unit_bittestmodel"."id" = 123)')
        else:
            expected = ('SELECT "unit_bittestmodel"."id", "unit_bittestmodel"."is_active" '
                        'FROM "unit_bittestmodel" '
                        'WHERE ("unit_bittestmodel"."is_active" = True AND "unit_bittestmodel"."id" = 123)')

        response = RetrieveSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, expected)

    def test_with_bad_lookup_value(self):
        self.kwargs['view_instance'].kwargs = {'id': "I'm ganna hack u are!"}
        response = RetrieveSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_queryset(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.none()
        response = RetrieveSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_result_set_raised(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(pk__in=[])
        response = RetrieveSqlQueryKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)


class RetrieveModelKeyBitTest(TestCase):
    def setUp(self):
        self.kwargs = {
            'params': None,
            'view_instance': Mock(),
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': None
        }
        self.kwargs['view_instance'].kwargs = {'id': 123}
        self.kwargs['view_instance'].lookup_field = 'id'
        self.kwargs['view_instance'].get_queryset = Mock(return_value=BitTestModel.objects.all())
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(is_active=True)

    def test_should_use_view__get_queryset__and_filter_it_with__filter_queryset__and_filter_by__lookup_field(self):
        model = BitTestModel.objects.create(is_active=True)
        self.kwargs['view_instance'].kwargs = {'id': model.id}

        expected = u"[(%s, True)]" % model.id

        response = RetrieveModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, expected)

    def test_with_bad_lookup_value(self):
        self.kwargs['view_instance'].kwargs = {'id': "I'm ganna hack u are!"}
        response = RetrieveModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_queryset(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.none()
        response = RetrieveModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)

    def test_should_return_none_if_empty_result_set_raised(self):
        self.kwargs['view_instance'].filter_queryset = lambda x: x.filter(pk__in=[])
        response = RetrieveModelKeyBit().get_data(**self.kwargs)
        self.assertEqual(response, None)


class ArgsKeyBitTest(TestCase):
    def setUp(self):
        self.test_args = ['abc', 'foobar', 'xyz']
        self.kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': None,
            'args': self.test_args,
            'kwargs': None
        }

    def test_with_no_args(self):
        self.assertEqual(ArgsKeyBit().get_data(**self.kwargs), [])

    def test_with_all_args(self):
        self.kwargs['params'] = '*'
        self.assertEqual(ArgsKeyBit().get_data(**self.kwargs), self.test_args)

    def test_with_specified_args(self):
        self.kwargs['params'] = test_arg_idx = [0, 2]
        expected_args = [self.test_args[i] for i in test_arg_idx]
        self.assertEqual(ArgsKeyBit().get_data(**self.kwargs), expected_args)

    def test_default_params_is_all_args(self):
        self.assertEqual(ArgsKeyBit().params, '*')


class KwargsKeyBitTest(TestCase):
    def setUp(self):
        self.test_kwargs = {
            'one': '1',
            'city': 'London',
        }
        self.kwargs = {
            'params': None,
            'view_instance': None,
            'view_method': None,
            'request': None,
            'args': None,
            'kwargs': self.test_kwargs,
        }

    def test_resulting_dict_all_kwargs(self):
        self.kwargs['params'] = '*'
        self.assertEqual(KwargsKeyBit().get_data(**self.kwargs), self.test_kwargs)

    def test_resulting_dict_specified_kwargs(self):
        keys = ['one', 'not_existing_param']
        expected_kwargs = {'one': self.test_kwargs['one']}
        self.kwargs['params'] = keys
        self.assertEqual(KwargsKeyBit().get_data(**self.kwargs), expected_kwargs)

    def test_resulting_dict_no_kwargs(self):
        self.assertEqual(KwargsKeyBit().get_data(**self.kwargs), {})

    def test_default_params_is_all_args(self):
        self.assertEqual(KwargsKeyBit().params, '*')
