# -*- coding: utf-8 -*-
from rest_framework_extensions.etag.decorators import etag, api_etag
from rest_framework_extensions.settings import extensions_api_settings


class BaseETAGMixin(object):
    # todo: test me. Create generic test like test_etag(view_instance, method, should_rebuild_after_method_evaluation)
    object_etag_func = extensions_api_settings.DEFAULT_OBJECT_ETAG_FUNC
    list_etag_func = extensions_api_settings.DEFAULT_LIST_ETAG_FUNC


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


class APIBaseETAGMixin(object):
    # todo: test me. Create generic test like test_etag(view_instance, method, should_rebuild_after_method_evaluation)
    api_object_etag_func = extensions_api_settings.DEFAULT_API_OBJECT_ETAG_FUNC
    api_list_etag_func = extensions_api_settings.DEFAULT_API_LIST_ETAG_FUNC


class APIListETAGMixin(APIBaseETAGMixin):
    @api_etag(etag_func='api_list_etag_func')
    def list(self, request, *args, **kwargs):
        return super(APIListETAGMixin, self).list(request, *args, **kwargs)


class APIRetrieveETAGMixin(APIBaseETAGMixin):
    @api_etag(etag_func='api_object_etag_func')
    def retrieve(self, request, *args, **kwargs):
        return super(APIRetrieveETAGMixin, self).retrieve(request, *args, **kwargs)


class APIUpdateETAGMixin(APIBaseETAGMixin):
    @api_etag(etag_func='api_object_etag_func', rebuild_after_method_evaluation=True)
    def update(self, request, *args, **kwargs):
        return super(APIUpdateETAGMixin, self).update(request, *args, **kwargs)


class APIDestroyETAGMixin(APIBaseETAGMixin):
    @api_etag(etag_func='api_object_etag_func')
    def destroy(self, request, *args, **kwargs):
        return super(APIDestroyETAGMixin, self).destroy(request, *args, **kwargs)


class APIReadOnlyETAGMixin(APIRetrieveETAGMixin,
                           APIListETAGMixin):
    pass


class APIETAGMixin(APIRetrieveETAGMixin,
                   APIUpdateETAGMixin,
                   APIDestroyETAGMixin,
                   APIListETAGMixin):
    pass
