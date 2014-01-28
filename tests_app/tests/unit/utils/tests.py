# -*- coding: utf-8 -*-
from mock import patch, Mock

from rest_framework import VERSION

from django.test import TestCase

from rest_framework_extensions.utils import (
    get_rest_framework_version,
    get_rest_framework_features,
    prepare_header_name,
)


class Test_get_rest_framework_version(TestCase):
    def test(self):
        expected = tuple(map(int, VERSION.split('.')))
        self.assertEqual(get_rest_framework_version(), expected)


class Test_get_rest_framework_features(TestCase):
    def test_router_trailing_slash(self):
        experiments = [
            {
                'version': (2, 3),
                'expected': False
            },
            {
                'version': (2, 3, 5),
                'expected': False
            },
            {
                'version': (2, 3, 6),
                'expected': True
            },
            {
                'version': (2, 3, 7),
                'expected': True
            },
            {
                'version': (2, 4),
                'expected': True
            },
        ]

        for exp in experiments:
            with patch('rest_framework_extensions.utils.get_rest_framework_version', Mock(return_value=exp['version'])):
                self.assertEqual(get_rest_framework_features()['router_trailing_slash'], exp['expected'])

    def test_allow_dot_in_lookup_regex_without_trailing_slash(self):
        experiments = [
            {
                'version': (2, 3),
                'expected': False
            },
            {
                'version': (2, 3, 5),
                'expected': False
            },
            {
                'version': (2, 3, 6),
                'expected': False
            },
            {
                'version': (2, 3, 7),
                'expected': False
            },
            {
                'version': (2, 3, 8),
                'expected': True
            },
            {
                'version': (2, 3, 9),
                'expected': True
            },
            {
                'version': (2, 3, 10),
                'expected': True
            },
            {
                'version': (2, 4),
                'expected': True
            },
        ]

        for exp in experiments:
            with patch('rest_framework_extensions.utils.get_rest_framework_version', Mock(return_value=exp['version'])):
                self.assertEqual(
                    get_rest_framework_features()['allow_dot_in_lookup_regex_without_trailing_slash'],
                    exp['expected']
                )


class Test_prepare_header_name(TestCase):
    def test_upper(self):
        self.assertEqual(prepare_header_name('Accept'), 'HTTP_ACCEPT')

    def test_replace_dash_with_underscores(self):
        self.assertEqual(prepare_header_name('Accept-Language'), 'HTTP_ACCEPT_LANGUAGE')

    def test_strips_whitespaces(self):
        self.assertEqual(prepare_header_name('  Accept-Language  '), 'HTTP_ACCEPT_LANGUAGE')

    def test_adds_http_prefix(self):
        self.assertEqual(prepare_header_name('Accept-Language'), 'HTTP_ACCEPT_LANGUAGE')