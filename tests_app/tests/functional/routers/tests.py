# -*- coding: utf-8 -*-
from django.test import TestCase

from rest_framework_extensions.compat_drf import get_lookup_allowed_symbols
from rest_framework_extensions.utils import get_rest_framework_features
from rest_framework_extensions.routers import ExtendedSimpleRouter

from tests_app.testutils import get_url_pattern_by_regex_pattern
from .views import RouterViewSet


class TestTrailingSlashIncluded(TestCase):
    def test_urls_have_trailing_slash_by_default(self):
        router = ExtendedSimpleRouter()
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        lookup_allowed_symbols = get_lookup_allowed_symbols()

        for exp in ['^router-viewset/$',
                    '^router-viewset/{0}/$'.format(lookup_allowed_symbols),
                    '^router-viewset/list_controller/$',
                    '^router-viewset/{0}/detail_controller/$'.format(lookup_allowed_symbols)]:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)


class TestTrailingSlashRemoved(TestCase):
    def test_urls_can_have_trailing_slash_removed(self):
        router = ExtendedSimpleRouter(trailing_slash=False)
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        lookup_allowed_symbols = get_lookup_allowed_symbols(
            force_dot=get_rest_framework_features()['allow_dot_in_lookup_regex_without_trailing_slash']
        )

        for exp in ['^router-viewset$',
                    '^router-viewset/{0}$'.format(lookup_allowed_symbols),
                    '^router-viewset/list_controller$',
                    '^router-viewset/{0}/detail_controller$'.format(lookup_allowed_symbols)]:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)
