from functools import wraps

from django.http.response import HttpResponse
from django.utils.decorators import available_attrs


from rest_framework_extensions.settings import extensions_api_settings


def get_cache(alias):
    from django.core.cache import caches
    return caches[alias]


class CacheResponse:
    """
    Store/Receive and return cached `HttpResponse` based on DRF response.


    .. note::
        This decorator will render and discard the original DRF response in
        favor of Django's `HttpResponse`. The allows the cache to retain a
        smaller memory footprint and eliminates the need to re-render
        responses on each request. Furthermore it eliminates the risk for users
        to unknowingly cache whole Serializers and QuerySets.

    """
    def __init__(self,
                 timeout=None,
                 key_func=None,
                 cache=None,
                 cache_errors=None):
        if timeout is None:
            self.timeout = extensions_api_settings.DEFAULT_CACHE_RESPONSE_TIMEOUT
        else:
            self.timeout = timeout

        if key_func is None:
            self.key_func = extensions_api_settings.DEFAULT_CACHE_KEY_FUNC
        else:
            self.key_func = key_func

        if cache_errors is None:
            self.cache_errors = extensions_api_settings.DEFAULT_CACHE_ERRORS
        else:
            self.cache_errors = cache_errors

        self.cache = get_cache(cache or extensions_api_settings.DEFAULT_USE_CACHE)

    def __call__(self, func):
        this = self

        @wraps(func, assigned=available_attrs(func))
        def inner(self, request, *args, **kwargs):
            return this.process_cache_response(
                view_instance=self,
                view_method=func,
                request=request,
                args=args,
                kwargs=kwargs,
            )
        return inner

    def process_cache_response(self,
                               view_instance,
                               view_method,
                               request,
                               args,
                               kwargs):

        key = self.calculate_key(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs
        )

        timeout = self.calculate_timeout(view_instance=view_instance)

        response_triple = self.cache.get(key)
        if not response_triple:
            # render response to create and cache the content byte string
            response = view_method(view_instance, request, *args, **kwargs)
            response = view_instance.finalize_response(request, response, *args, **kwargs)
            response.render()

            if not response.status_code >= 400 or self.cache_errors:
                response_triple = (
                    response.rendered_content,
                    response.status_code,
                    response._headers.copy()
                )
                self.cache.set(key, response_triple, timeout)
        else:
            # build smaller Django HttpResponse
            content, status, headers = response_triple
            response = HttpResponse(content=content, status=status)
            response._headers = headers

        if not hasattr(response, '_closable_objects'):
            response._closable_objects = []

        return response

    def calculate_key(self,
                      view_instance,
                      view_method,
                      request,
                      args,
                      kwargs):
        if isinstance(self.key_func, str):
            key_func = getattr(view_instance, self.key_func)
        else:
            key_func = self.key_func
        return key_func(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs,
        )

    def calculate_timeout(self, view_instance, **_):
        if isinstance(self.timeout, str):
            self.timeout = getattr(view_instance, self.timeout)
        return self.timeout


cache_response = CacheResponse
