from copy import deepcopy
import hashlib
import json
from mock import Mock, patch

from django.test import TestCase

from rest_framework import viewsets

from rest_framework_extensions.key_constructor.constructors import (
    KeyConstructor,
)
from rest_framework_extensions.utils import get_unique_method_id
from rest_framework.test import APIRequestFactory

from tests_app.testutils import (
    override_extensions_api_settings,
    TestFormatKeyBit,
    TestUsedKwargsKeyBit,
    TestLanguageKeyBit,
)


factory = APIRequestFactory()


class KeyConstructorTest_bits(TestCase):
    def test_me(self):
        class MyKeyConstructor(KeyConstructor):
            format = TestFormatKeyBit()
            language = TestLanguageKeyBit()

        constructor_instance = MyKeyConstructor()
        expected = {
            'format': MyKeyConstructor.format,
            'language': MyKeyConstructor.language
        }
        self.assertEqual(constructor_instance.bits, expected)

    def test_with_inheritance(self):
        class MyKeyConstructor(KeyConstructor):
            format = TestFormatKeyBit()

        class ChildKeyConstructor(MyKeyConstructor):
            language = TestLanguageKeyBit()

        constructor_instance = ChildKeyConstructor()
        expected = {
            'format': ChildKeyConstructor.format,
            'language': ChildKeyConstructor.language
        }
        self.assertEqual(constructor_instance.bits, expected)


class KeyConstructorTest(TestCase):
    def setUp(self):
        class View(viewsets.ReadOnlyModelViewSet):
            pass

        view_intance = View()
        view_method = view_intance.retrieve

        self.kwargs = {
            'view_instance': view_intance,
            'view_method': view_method,
            'request': factory.get(''),
            'args': None,
            'kwargs': None
        }

    def test_prepare_key_consistency_for_equal_dicts_with_different_key_positions(self):
        class MyKeyConstructor(KeyConstructor):
            pass

        constructor_instance = MyKeyConstructor()
        one = {'used_kwargs': {'view_method': 'view_method', 'kwargs': None, 'view_instance': 'view_instance', 'params': {'hello': 'world'}, 'args': None, 'request': 'request'}}
        two = {'used_kwargs': {'params': {'hello': 'world'}, 'kwargs': None, 'view_method': 'view_method', 'view_instance': 'view_instance', 'args': None, 'request': 'request'}}
        self.assertEqual(one, two)
        self.assertEqual(constructor_instance.prepare_key(one), constructor_instance.prepare_key(two))

    def prepare_key(self, key_dict):
        return hashlib.md5(json.dumps(key_dict, sort_keys=True).encode('utf-8')).hexdigest()

    def test_key_construction__with_bits_without_params(self):
        class MyKeyConstructor(KeyConstructor):
            format = TestFormatKeyBit()
            language = TestLanguageKeyBit()

        constructor_instance = MyKeyConstructor()
        response = constructor_instance(**self.kwargs)
        expected = {
            'format': u'json',
            'language': u'ru',
        }
        self.assertEqual(response, self.prepare_key(expected))

    def test_key_construction__with_bits_with_params(self):
        class MyKeyConstructor(KeyConstructor):
            used_kwargs = TestUsedKwargsKeyBit(params={'hello': 'world'})

        with patch.object(json.JSONEncoder, 'default', Mock(return_value='force serializing')):
            constructor_instance = MyKeyConstructor()
            response = constructor_instance(**self.kwargs)
            expected_value = deepcopy(self.kwargs)
            expected_value['params'] = {'hello': 'world'}
            expected_data_from_bits = {
                'used_kwargs': expected_value
            }
            msg = 'Data from bits: {data_from_bits}\nExpected data from: {expected_data_from_bits}'.format(
                data_from_bits=json.dumps(constructor_instance.get_data_from_bits(**self.kwargs)),
                expected_data_from_bits=json.dumps(expected_data_from_bits)
            )

            self.assertEqual(response, self.prepare_key(expected_data_from_bits), msg=msg)

    def test_two_key_construction_with_same_bits_in_different_order_should_produce_equal_keys(self):
        class MyKeyConstructor_1(KeyConstructor):
            language = TestLanguageKeyBit()
            format = TestFormatKeyBit()

        class MyKeyConstructor_2(KeyConstructor):
            format = TestFormatKeyBit()
            language = TestLanguageKeyBit()

        self.assertEqual(
            MyKeyConstructor_1()(**self.kwargs),
            MyKeyConstructor_2()(**self.kwargs)
        )

    def test_key_construction__with_bits_with_params__and_with_constructor_with_params(self):
        class MyKeyConstructor(KeyConstructor):
            used_kwargs = TestUsedKwargsKeyBit(params={'hello': 'world'})

        with patch.object(json.JSONEncoder, 'default', Mock(return_value='force serializing')):
            constructor_instance = MyKeyConstructor(params={
                'used_kwargs': {'goodbye': 'moon'}
            })
            response = constructor_instance(**self.kwargs)
            expected_value = deepcopy(self.kwargs)
            expected_value['params'] = {'goodbye': 'moon'}
            expected_data_from_bits = {
                'used_kwargs': expected_value
            }
            msg = 'Data from bits: {data_from_bits}\nExpected data from: {expected_data_from_bits}'.format(
                data_from_bits=json.dumps(constructor_instance.get_data_from_bits(**self.kwargs)),
                expected_data_from_bits=json.dumps(expected_data_from_bits)
            )

            self.assertEqual(response, self.prepare_key(expected_data_from_bits), msg=msg)


class KeyConstructorTest___get_memoization_key(TestCase):
    def setUp(self):
        class View(viewsets.ReadOnlyModelViewSet):
            pass

        self.view_intance = View()
        self.view_method = self.view_intance.retrieve
        self.request = factory.get('')

    def test_me(self):
        class MyKeyConstructor(KeyConstructor):
            language = TestLanguageKeyBit()
            format = TestFormatKeyBit()

        constructor_instance = MyKeyConstructor()
        response = constructor_instance._get_memoization_key(
            view_instance=self.view_intance,
            view_method=self.view_method,
            args=[1, 2, 3, u'Привет мир'],
            kwargs={1: 2, 3: 4, u'привет': u'мир'}
        )
        expected = json.dumps({
            'unique_method_id': get_unique_method_id(view_instance=self.view_intance, view_method=self.view_method),
            'args': [1, 2, 3, u'Привет мир'],
            'kwargs': {1: 2, 3: 4, u'привет': u'мир'},
            'instance_id': id(constructor_instance)
        })
        self.assertEqual(response, expected)


class KeyConstructorTestBehavior__memoization(TestCase):
    def setUp(self):
        class View(viewsets.ReadOnlyModelViewSet):
            pass

        class MyKeyConstructor(KeyConstructor):
            format = TestFormatKeyBit()
            language = TestLanguageKeyBit()

        view_intance = View()
        view_method = view_intance.retrieve

        self.MyKeyConstructor = MyKeyConstructor
        self.kwargs = {
            'view_instance': view_intance,
            'view_method': view_method,
            'request': factory.get(''),
            'args': None,
            'kwargs': None
        }

    def test_should_not_memoize_by_default(self):
        constructor_instance = self.MyKeyConstructor()
        response_1 = constructor_instance(**self.kwargs)
        response_2 = constructor_instance(**self.kwargs)
        self.assertFalse(response_1 is response_2)

    def test_should_memoize_if_asked(self):
        constructor_instance = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance(**self.kwargs)
        response_2 = constructor_instance(**self.kwargs)
        self.assertTrue(response_1 is response_2)

    def test_should_use_value_from_settings_for_default_memoize_boolean_value(self):
        with override_extensions_api_settings(DEFAULT_KEY_CONSTRUCTOR_MEMOIZE_FOR_REQUEST=True):
            constructor_instance = KeyConstructor()
            self.assertTrue(constructor_instance.memoize_for_request)

        with override_extensions_api_settings(DEFAULT_KEY_CONSTRUCTOR_MEMOIZE_FOR_REQUEST=False):
            constructor_instance = KeyConstructor()
            self.assertFalse(constructor_instance.memoize_for_request)

    def test_should_memoize_in_request_instance(self):
        constructor_instance = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance(**self.kwargs)
        self.kwargs['request'] = factory.get('')
        response_2 = constructor_instance(**self.kwargs)
        self.assertFalse(response_1 is response_2)

    def test_should_use_different_memoization_for_different_arguments(self):
        constructor_instance = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance(**self.kwargs)
        response_2 = constructor_instance(**self.kwargs)
        self.assertTrue(response_1 is response_2)

        self.kwargs['args'] = [1, 2, 3, u'привет мир']
        response_3 = constructor_instance(**self.kwargs)
        response_4 = constructor_instance(**self.kwargs)
        self.assertTrue(response_3 is response_4)

        self.assertFalse(response_1 is response_3)
        self.assertFalse(response_1 is response_4)
        self.assertFalse(response_2 is response_3)
        self.assertFalse(response_2 is response_4)

    def test_should_use_different_memoization_for_different_request_instances(self):
        constructor_instance = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance(**self.kwargs)
        self.kwargs['request'] = factory.get('')
        response_2 = constructor_instance(**self.kwargs)
        self.assertFalse(response_1 is response_2)

    def test_should_use_different_memoization_for_different_constructor_instances(self):
        constructor_instance_1 = self.MyKeyConstructor(memoize_for_request=True)
        constructor_instance_2 = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance_1(**self.kwargs)
        response_2 = constructor_instance_2(**self.kwargs)
        self.assertFalse(response_1 is response_2)

    def test_should_use_different_memoization_for_different_views_with_same_method(self):
        class View_2(viewsets.ReadOnlyModelViewSet):
            pass

        constructor_instance = self.MyKeyConstructor(memoize_for_request=True)
        response_1 = constructor_instance(**self.kwargs)

        view_2_instance = View_2()
        self.kwargs['view_instance'] = view_2_instance
        self.kwargs['view_instance'] = view_2_instance.retrieve
        response_2 = constructor_instance(**self.kwargs)
        self.assertFalse(response_1 is response_2)
