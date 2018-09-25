import contextlib
try:
    from unittest import mock
except ImportError:
    import mock

from django.test import TestCase

from rest_framework_extensions.utils import prepare_header_name, get_rest_framework_version


@contextlib.contextmanager
def parsed_version(version):
    with mock.patch('rest_framework.VERSION', version):
        yield get_rest_framework_version()


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

    def test_get_rest_framework_version_exotic_version(self):
        """See <https://github.com/chibisov/drf-extensions/pull/198>"""
        with parsed_version('1.2alphaSOMETHING') as version:
            self.assertEqual(version, (1, 2, 'alpha', 'SOMETHING'))

    def test_get_rest_framework_version_normal_version(self):
        """See <https://github.com/chibisov/drf-extensions/pull/198>"""
        with parsed_version('3.14.16') as version:
            self.assertEqual(version, (3, 14, 16))
