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