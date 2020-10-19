import base64
from mock import patch

from rest_framework import HTTP_HEADER_ENCODING

from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import KeyConstructor


def get_url_pattern_by_regex_pattern(patterns, pattern_string):
    # todo: test me
    for pattern in patterns:
        if pattern.pattern.regex.pattern == pattern_string:
            return pattern


def override_extensions_api_settings(**kwargs):
    return patch.multiple(
        'rest_framework_extensions.settings.extensions_api_settings',
        **kwargs
    )


def basic_auth_header(username, password):
    credentials = ('%s:%s' % (username, password))
    base64_credentials = base64.b64encode(
        credentials.encode(HTTP_HEADER_ENCODING)
    ).decode(HTTP_HEADER_ENCODING)
    return 'Basic %s' % base64_credentials


class TestFormatKeyBit(bits.KeyBitBase):
    def get_data(self, **kwargs):
        return u'json'


class TestLanguageKeyBit(bits.KeyBitBase):
    def get_data(self, **kwargs):
        return u'ru'


class TestUsedKwargsKeyBit(bits.KeyBitBase):
    def get_data(self, **kwargs):
        return kwargs


class TestKeyConstructor(KeyConstructor):
    format = TestFormatKeyBit()
    language = TestLanguageKeyBit()
