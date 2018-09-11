# -*- coding: utf-8 -*-
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.settings import extensions_api_settings


class BaseCacheResponseMixin(object):
    # todo: test me. Create generic test like
    # test_cache_reponse(view_instance, method, should_rebuild_after_method_evaluation)
    object_cache_key_func = extensions_api_settings.DEFAULT_OBJECT_CACHE_KEY_FUNC
    list_cache_key_func = extensions_api_settings.DEFAULT_LIST_CACHE_KEY_FUNC


class ListCacheResponseMixin(BaseCacheResponseMixin):
    @cache_response(key_func='list_cache_key_func')
    def list(self, request, *args, **kwargs):
        return super(ListCacheResponseMixin, self).list(request, *args, **kwargs)


class RetrieveCacheResponseMixin(BaseCacheResponseMixin):
    @cache_response(key_func='object_cache_key_func')
    def retrieve(self, request, *args, **kwargs):
        return super(RetrieveCacheResponseMixin, self).retrieve(request, *args, **kwargs)


class CacheResponseMixin(RetrieveCacheResponseMixin,
                         ListCacheResponseMixin):
    pass