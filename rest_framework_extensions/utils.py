# -*- coding: utf-8 -*-
import itertools
from functools import wraps

from django import VERSION as django_version

import rest_framework

from rest_framework_extensions.key_constructor.constructors import (
    DefaultKeyConstructor,
    DefaultObjectKeyConstructor,
    DefaultListKeyConstructor,
)


def get_rest_framework_features():
    return {
        'router_trailing_slash': get_rest_framework_version() >= (2, 3, 6),
        'allow_dot_in_lookup_regex_without_trailing_slash': get_rest_framework_version() >= (2, 3, 8),
        'use_dot_in_lookup_regex_by_default': get_rest_framework_version() >= (2, 4, 0),
        'max_paginate_by': get_rest_framework_version() >= (2, 3, 8),
        'django_object_permissions_class': get_rest_framework_version() >= (2, 3, 8),
        'save_related_serializers': get_rest_framework_version() >= (2, 3, 8),
        'write_only_fields': get_rest_framework_version() >= (2, 3, 11),
        'has_action_and_link_decorators': get_rest_framework_version() < (3, 0),
        'has_auto_writable_nested_serialization': get_rest_framework_version() < (3, 0),
        'uses_single_request_data_in_serializers': get_rest_framework_version() >= (3, 0),
        'allows_to_send_custom_kwargs_for_saving_object_in_serializers': get_rest_framework_version() <= (3, 0),
        'uses_single_request_data_in_serializers': get_rest_framework_version() >= (3, 0),
        'single_step_object_creation_in_serializers': get_rest_framework_version() >= (3, 0),
    }


def get_django_features():
    # todo: test me
    return {
        'caches_singleton': django_version >= (1, 7, 0)
    }


def get_rest_framework_version():
    return tuple(map(int, rest_framework.VERSION.split('.')))


def flatten(list_of_lists):
    """
    Takes an iterable of iterables,
    returns a single iterable containing all items
    """
    # todo: test me
    return itertools.chain(*list_of_lists)


def prepare_header_name(name):
    """
    >> prepare_header_name('Accept-Language')
    http_accept_language
    """
    return 'http_{0}'.format(name.strip().replace('-', '_')).upper()


def get_unique_method_id(view_instance, view_method):
    # todo: test me as UniqueMethodIdKeyBit
    return u'.'.join([
        view_instance.__module__,
        view_instance.__class__.__name__,
        view_method.__name__
    ])


def get_model_opts_concrete_fields(opts):
    # todo: test me
    if not hasattr(opts, 'concrete_fields'):
        opts.concrete_fields = [f for f in opts.fields if f.column is not None]
    return opts.concrete_fields



default_cache_key_func = DefaultKeyConstructor()
default_object_cache_key_func = DefaultObjectKeyConstructor()
default_list_cache_key_func = DefaultListKeyConstructor()

default_etag_func = default_cache_key_func
default_object_etag_func = default_object_cache_key_func
default_list_etag_func = default_list_cache_key_func
