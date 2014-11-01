"""
The `compat` module provides support for backwards compatibility with older
versions of Django REST Framework.
"""
from rest_framework_extensions.utils import get_rest_framework_features


def add_trailing_slash_if_needed(regexp_string):
    # todo: test me
    if get_rest_framework_features()['router_trailing_slash']:
        return regexp_string[:-2] + '{trailing_slash}$'
    else:
        return regexp_string


def get_lookup_allowed_symbols(kwarg_name='pk', force_dot=False):
    # todo: test me
    if get_rest_framework_features()['use_dot_in_lookup_regex_by_default'] or force_dot:
        return '(?P<{0}>[^/.]+)'.format(kwarg_name)
    else:
        return '(?P<{0}>[^/]+)'.format(kwarg_name)