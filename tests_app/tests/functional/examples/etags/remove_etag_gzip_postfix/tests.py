# -*- coding: utf-8 -*-
from django.test import TestCase
from django.conf.urls import url
from django.test.utils import override_settings

from .views import MyView


class RemoveEtagGzipPostfixTest(TestCase):
    urls = (
        url(r'^remove-etag-gzip-postfix/$', MyView.as_view()),
    )

    @override_settings(MIDDLEWARE_CLASSES=(
        'django.middleware.gzip.GZipMiddleware',
        'django.middleware.common.CommonMiddleware'
    ))
    def test_without_middleware(self):
        response = self.client.get('/remove-etag-gzip-postfix/', **{
            'HTTP_ACCEPT_ENCODING': 'gzip'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['ETag'], '"etag_value;gzip"')

    @override_settings(MIDDLEWARE_CLASSES=(
        'tests_app.tests.functional.examples.etags.remove_etag_gzip_postfix.middleware.RemoveEtagGzipPostfix',
        'django.middleware.gzip.GZipMiddleware',
        'django.middleware.common.CommonMiddleware'
    ))
    def test_with_middleware(self):
        response = self.client.get('/remove-etag-gzip-postfix/', **{
            'HTTP_ACCEPT_ENCODING': 'gzip'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['ETag'], '"etag_value"')