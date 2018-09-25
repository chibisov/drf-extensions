from django.test import TestCase

from rest_framework_extensions.routers import ExtendedSimpleRouter

from tests_app.testutils import get_url_pattern_by_regex_pattern
from .views import RouterViewSet


class TestTrailingSlashIncluded(TestCase):
    def test_urls_have_trailing_slash_by_default(self):
        router = ExtendedSimpleRouter()
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        for exp in ['^router-viewset/$',
                    '^router-viewset/(?P<pk>[^/.]+)/$',
                    '^router-viewset/list_controller/$',
                    '^router-viewset/(?P<pk>[^/.]+)/detail_controller/$']:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)


class TestTrailingSlashRemoved(TestCase):
    def test_urls_can_have_trailing_slash_removed(self):
        router = ExtendedSimpleRouter(trailing_slash=False)
        router.register(r'router-viewset', RouterViewSet)
        urls = router.urls

        for exp in ['^router-viewset$',
                    '^router-viewset/(?P<pk>[^/.]+)$',
                    '^router-viewset/list_controller$',
                    '^router-viewset/(?P<pk>[^/.]+)/detail_controller$']:
            msg = 'Should find url pattern with regexp %s' % exp
            self.assertIsNotNone(get_url_pattern_by_regex_pattern(urls, exp), msg=msg)
