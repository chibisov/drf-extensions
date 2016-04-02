"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals

import django
import inspect
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

# Try to import six from Django, fallback to included `six`.
from django.utils import six


# location of patterns, url, include changes in 1.8 onwards

from django.conf.urls import url, include


from django.utils.encoding import smart_text

from django.utils.encoding import force_text



# HttpResponseBase only exists from 1.5 onwards

from django.http.response import HttpResponseBase


# django-filter is optional
try:
    import django_filters
except ImportError:
    django_filters = None

# guardian is optional
try:
    import guardian
except ImportError:
    guardian = None


# cStringIO only if it's available, otherwise StringIO
try:
    import cStringIO.StringIO as StringIO
except ImportError:
    StringIO = six.StringIO

BytesIO = six.BytesIO


# urlparse compat import (Required because it changed in python 3.x)
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

# UserDict moves in Python 3
try:
    from UserDict import UserDict
    from UserDict import DictMixin
except ImportError:
    from collections import UserDict
    from collections import MutableMapping as DictMixin

# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None


def get_model_name(model_cls):
    return model_cls._meta.model_name
    
def get_concrete_model(model_cls):
    return model_cls._meta.concrete_model



# PUT, DELETE do not require CSRF until 1.4. They should.Make it better.

from django.middleware.csrf import CsrfViewMiddleware


# timezone support is new in Django 1.4
try:
    from django.utils import timezone
except ImportError:
    timezone = None

# dateparse is ALSO new in Django 1.4

from django.utils.dateparse import parse_date, parse_datetime, parse_time



# smart_urlquote is new on Django 1.4

from django.utils.html import smart_urlquote


# RequestFactory only provide `generic` from 1.5 onwards

from django.test.client import RequestFactory
from django.test.client import FakePayload



# Markdown is optional
try:
    import markdown

    def apply_markdown(text):
        """
        Simple wrapper around :func:`markdown.markdown` to set the base level
        of '#' style headers to <h2>.
        """

        extensions = ['headerid(level=2)']
        safe_mode = False
        md = markdown.Markdown(extensions=extensions, safe_mode=safe_mode)
        return md.convert(text)

except ImportError:
    apply_markdown = None


# Yaml is optional
try:
    import yaml
except ImportError:
    yaml = None


# XML is optional
try:
    import defusedxml.ElementTree as etree
except ImportError:
    etree = None

# OAuth is optional
try:
    # Note: The `oauth2` package actually provides oauth1.0a support.  Urg.
    import oauth2 as oauth
except ImportError:
    oauth = None

# OAuth is optional
try:
    import oauth_provider
    from oauth_provider.store import store as oauth_provider_store

    # check_nonce's calling signature in django-oauth-plus changes sometime
    # between versions 2.0 and 2.2.1
    def check_nonce(request, oauth_request, oauth_nonce, oauth_timestamp):
        check_nonce_args = inspect.getargspec(oauth_provider_store.check_nonce).args
        if 'timestamp' in check_nonce_args:
            return oauth_provider_store.check_nonce(
                request, oauth_request, oauth_nonce, oauth_timestamp
            )
        return oauth_provider_store.check_nonce(
            request, oauth_request, oauth_nonce
        )

except (ImportError, ImproperlyConfigured):
    oauth_provider = None
    oauth_provider_store = None
    check_nonce = None

# OAuth 2 support is optional
try:
    import provider as oauth2_provider
    from provider import scope as oauth2_provider_scope
    from provider import constants as oauth2_constants
    if oauth2_provider.__version__ in ('0.2.3', '0.2.4'):
        # 0.2.3 and 0.2.4 are supported version that do not support
        # timezone aware datetimes
        import datetime
        provider_now = datetime.datetime.now
    else:
        # Any other supported version does use timezone aware datetimes
        from django.utils.timezone import now as provider_now
except ImportError:
    oauth2_provider = None
    oauth2_provider_scope = None
    oauth2_constants = None
    provider_now = None

# Handle lazy strings
from django.utils.functional import Promise

if six.PY3:
    def is_non_str_iterable(obj):
        if (isinstance(obj, str) or
            (isinstance(obj, Promise) and obj._delegate_text)):
            return False
        return hasattr(obj, '__iter__')
else:
    def is_non_str_iterable(obj):
        return hasattr(obj, '__iter__')

