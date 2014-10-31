# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils.encoding import force_text

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

    def test_cache_key_should_differ_with_query_param(self):
        resp = self.client.get('/hello-param/?param=world')
        self.assertEqual(force_text(resp.content), '"Hello world"')

        resp = self.client.get('/hello-param/?param=everyone')
        self.assertEqual(force_text(resp.content), '"Hello everyone"')
