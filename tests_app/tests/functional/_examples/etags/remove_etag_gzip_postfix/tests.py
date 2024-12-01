from django.test import TestCase, override_settings
from django.conf import settings

@override_settings(ROOT_URLCONF='tests_app.tests.functional._examples.etags.remove_etag_gzip_postfix.urls')
class RemoveEtagGzipPostfixTest(TestCase):

    @override_settings(MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.gzip.GZipMiddleware',
    ))
    def test_without_middleware(self):
        response = self.client.get('/remove-etag-gzip-postfix/', **{
            'HTTP_ACCEPT_ENCODING': 'gzip'
        })

        self.assertEqual(response.status_code, 200)
        # previously it was '"etag_value;gzip"' , instead of '"etag_value"', gzip don't append ;gzip suffix after encoding 
        self.assertEqual(response['ETag'], '"etag_value"')

    @override_settings(MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.gzip.GZipMiddleware',
        'tests_app.tests.functional._examples.etags.remove_etag_gzip_postfix.middleware.RemoveEtagGzipPostfix',
    ))
    def test_with_middleware(self):
        response = self.client.get('/remove-etag-gzip-postfix/', **{
            'HTTP_ACCEPT_ENCODING': 'gzip'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['ETag'], '"etag_value"')
