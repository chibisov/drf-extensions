# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from rest_framework_extensions.compat import force_text

from .urls import urlpatterns


class TestCacheResponseFunctionally(TestCase):
    urls = urlpatterns

    def test_should_return_response(self):
        resp = self.client.get('/hello/')
        self.assertEqual(force_text(resp.content), '"Hello world"')

    def test_should_return_same_response_if_cached(self):
        resp_1 = self.client.get('/hello/')
        resp_2 = self.client.get('/hello/')
        self.assertEqual(resp_1.content, resp_2.content)
