from django.test import TestCase, override_settings
from django.utils.encoding import force_str


@override_settings(ROOT_URLCONF='tests_app.tests.functional.cache.decorators.urls')
class TestCacheResponseFunctionally(TestCase):

    def test_should_return_response(self):
        resp = self.client.get('/hello/')
        self.assertEqual(force_str(resp.content), '"Hello world"')

    def test_should_return_same_response_if_cached(self):
        resp_1 = self.client.get('/hello/')
        resp_2 = self.client.get('/hello/')
        self.assertEqual(resp_1.content, resp_2.content)
