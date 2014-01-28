# -*- coding: utf-8 -*-
from mock import patch

from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import KeyConstructor


def get_url_pattern_by_regex_pattern(patterns, pattern_string):
    # todo: test me
    for pattern in patterns:
        if pattern.regex.pattern == pattern_string:
            return pattern


def override_extensions_api_settings(**kwargs):
    return patch.multiple(
        'rest_framework_extensions.settings.extensions_api_settings',
        **kwargs
    )


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