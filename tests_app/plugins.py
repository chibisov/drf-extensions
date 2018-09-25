import shutil
import os

from django_nose.plugin import AlwaysOnPlugin

from django.test import TestCase
from django.core.cache import cache
from django.conf import settings


class UnitTestDiscoveryPlugin(AlwaysOnPlugin):
    """
    Enables unittest compatibility mode (dont test functions, only TestCase
    subclasses, and only methods that start with [Tt]est).
    """
    enabled = True

    def wantModule(self, module):
        return True

    def wantFile(self, file):
        if file.endswith('.py'):
            return True

    def wantClass(self, cls):
        if not issubclass(cls, TestCase):
            return False

    def wantMethod(self, method):
        if not method.__name__.lower().startswith('test'):
            return False

    def wantFunction(self, function):
        return False


class PrepareRestFrameworkSettingsPlugin(AlwaysOnPlugin):
    def begin(self):
        self._monkeypatch_default_settings()

    def _monkeypatch_default_settings(self):
        from rest_framework import settings

        PATCH_REST_FRAMEWORK = {
            # Testing
            'TEST_REQUEST_RENDERER_CLASSES': (
                'rest_framework.renderers.MultiPartRenderer',
                'rest_framework.renderers.JSONRenderer'
            ),
            'TEST_REQUEST_DEFAULT_FORMAT': 'multipart',
        }

        for key, value in PATCH_REST_FRAMEWORK.items():
            if key not in settings.DEFAULTS:
                settings.DEFAULTS[key] = value


class PrepareFileStorageDir(AlwaysOnPlugin):
    def begin(self):
        if not os.path.isdir(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)

    def finalize(self, result):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)


class FlushCache(AlwaysOnPlugin):
    # startTest didn't work :(
    def begin(self):
        self._monkeypatch_testcase()

    def _monkeypatch_testcase(self):
        old_run = TestCase.run

        def new_run(*args, **kwargs):
            cache.clear()
            return old_run(*args, **kwargs)
        TestCase.run = new_run
