# -*- coding: utf-8 -*-
from mock import patch, Mock

from rest_framework import VERSION

from django.test import TestCase

from rest_framework_extensions.utils import (
    get_rest_framework_version,
    get_rest_framework_features,
    prepare_header_name,
)


class TestRestFrameworkVersion(TestCase):
    def test(self):
        expected = tuple(map(int, VERSION.split('.')))
        self.assertEqual(get_rest_framework_version(), expected)


class TestRestFrameworkFeatures(TestCase):
    pass

class TestPrepareHeaderName(TestCase):
    def test_upper(self):
        self.assertEqual(prepare_header_name('Accept'), 'HTTP_ACCEPT')

    def test_replace_dash_with_underscores(self):
        self.assertEqual(
            prepare_header_name('Accept-Language'), 'HTTP_ACCEPT_LANGUAGE')

    def test_strips_whitespaces(self):
        self.assertEqual(
            prepare_header_name('  Accept-Language  '), 'HTTP_ACCEPT_LANGUAGE')

    def test_adds_http_prefix(self):
        self.assertEqual(
            prepare_header_name('Accept-Language'), 'HTTP_ACCEPT_LANGUAGE')
