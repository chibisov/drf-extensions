# -*- coding: utf-8 -*-
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.settings import extensions_api_settings


class BaseETAGMixin(object):
    # todo: test me. Create generic test like test_etag(view_instance, method, should_rebuild_after_method_evaluation)
    object_etag_func = extensions_api_settings.DEFAULT_OBJECT_ETAG_FUNC
    list_etag_func = extensions_api_settings.DEFAULT_LIST_ETAG_FUNC

    # Default functions to compute the ETags from (a list of) individual API resources.
    # The default functions *DO NOT* consider the request method or view instance, but only the queried resources.
    api_object_etag_func = extensions_api_settings.DEFAULT_API_OBJECT_ETAG_FUNC
    api_list_etag_func = extensions_api_settings.DEFAULT_API_LIST_ETAG_FUNC


class ListETAGMixin(BaseETAGMixin):
    @etag(etag_func='list_etag_func')
    def list(self, request, *args, **kwargs):
        return super(ListETAGMixin, self).list(request, *args, **kwargs)


class RetrieveETAGMixin(BaseETAGMixin):
    @etag(etag_func='object_etag_func')
    def retrieve(self, request, *args, **kwargs):
        return super(RetrieveETAGMixin, self).retrieve(request, *args, **kwargs)


class UpdateETAGMixin(BaseETAGMixin):
    @etag(etag_func='object_etag_func', rebuild_after_method_evaluation=True)
    def update(self, request, *args, **kwargs):
        return super(UpdateETAGMixin, self).update(request, *args, **kwargs)


class DestroyETAGMixin(BaseETAGMixin):
    @etag(etag_func='object_etag_func')
    def destroy(self, request, *args, **kwargs):
        return super(DestroyETAGMixin, self).destroy(request, *args, **kwargs)


class ReadOnlyETAGMixin(RetrieveETAGMixin,
                        ListETAGMixin):
    pass


class ETAGMixin(RetrieveETAGMixin,
                UpdateETAGMixin,
                DestroyETAGMixin,
                ListETAGMixin):
    pass


class APIListETAGMixin(BaseETAGMixin):
    @etag(etag_func='api_list_etag_func')
    def list(self, request, *args, **kwargs):
        return super(APIListETAGMixin, self).list(request, *args, **kwargs)


class APIRetrieveETAGMixin(BaseETAGMixin):
    @etag(etag_func='api_object_etag_func')
    def retrieve(self, request, *args, **kwargs):
        return super(APIRetrieveETAGMixin, self).retrieve(request, *args, **kwargs)


class APIUpdateETAGMixin(BaseETAGMixin):
    """
    A mixin that principally *allows* a conditional request for an update (PUT/PATCH) operation.
    The resource version is optionally provided as `ETag` using the `If-Match` HTTP header.
    If the header is not present, the operation may succeed anyway.
    """
    @etag(etag_func='api_object_etag_func', rebuild_after_method_evaluation=True)
    def update(self, request, *args, **kwargs):
        return super(APIUpdateETAGMixin, self).update(request, *args, **kwargs)


class APIDestroyETAGMixin(BaseETAGMixin):
    """
    A mixin that principally *allows* a conditional request for a delete (DELETE) operation.
    The resource version is optionally provided as `ETag` using the `If-Match` HTTP header.
    If the header is not present, the operation may succeed anyway.
    """
    @etag(etag_func='api_object_etag_func')
    def destroy(self, request, *args, **kwargs):
        return super(APIDestroyETAGMixin, self).destroy(request, *args, **kwargs)


class APIReadOnlyETAGMixin(APIRetrieveETAGMixin,
                           APIListETAGMixin):
    pass


class APIETAGMixin(APIListETAGMixin,
                   APIRetrieveETAGMixin,
                   APIUpdateETAGMixin,
                   APIDestroyETAGMixin):
    """
    A mixin that principally *allows* optimistic concurrency control (OCC) using `ETag`s for DRF API views and viewsets.

    NB: Update and delete operations are *NOT* required to be conditional! Use `OCCAPIETAGMixin` to enforce
    the default pre-conditional header checks for update and delete.
    """
    pass
