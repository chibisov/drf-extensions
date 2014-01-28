# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import unittest

from rest_framework_extensions.utils import get_rest_framework_features
from rest_framework_extensions.routers import ExtendedSimpleRouter

from tests_app.testutils import get_url_pattern_by_regex_pattern
from .views import RouterViewSet


class TestTrailingSlashIncluded(TestCase):
    def test_urls_have_trailing_slash_by_default(self):
        router = ExtendedSimpleRouter()
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        for exp in ['^router-viewset/$',
                    '^router-viewset/(?P<pk>[^/]+)/$',
                    '^router-viewset/list_controller/$',
                    '^router-viewset/(?P<pk>[^/]+)/detail_controller/$']:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)


@unittest.skipUnless(
    get_rest_framework_features()['router_trailing_slash'],
    "Current DRF version doesn't support Router trailing_slash"
)
class TestTrailingSlashRemoved(TestCase):
    def test_urls_can_have_trailing_slash_removed(self):
        router = ExtendedSimpleRouter(trailing_slash=False)
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        if get_rest_framework_features()['allow_dot_in_lookup_regex_without_trailing_slash']:
            lookup_allowed_symbols = '(?P<pk>[^/.]+)'
        else:
            lookup_allowed_symbols = '(?P<pk>[^/]+)'

        for exp in ['^router-viewset$',
                    '^router-viewset/' + lookup_allowed_symbols + r'$',
                    '^router-viewset/list_controller$',
                    '^router-viewset/' + lookup_allowed_symbols + '/detail_controller$']:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)