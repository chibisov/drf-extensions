# -*- coding: utf-8 -*-

from django.test import TestCase

from rest_framework_extensions.utils import prepare_header_name


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
