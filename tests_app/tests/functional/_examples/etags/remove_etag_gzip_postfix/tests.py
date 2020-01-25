from django.test import TestCase, override_settings


@override_settings(ROOT_URLCONF='tests_app.tests.functional.examples.etags.remove_etag_gzip_postfix.urls')
class RemoveEtagGzipPostfixTest(TestCase):

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
