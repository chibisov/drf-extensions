# -*- coding: utf-8 -*-
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework_extensions.etag.mixins import ReadOnlyETAGMixin, ETAGMixin
from rest_framework_extensions.utils import get_rest_framework_features
from rest_framework_extensions.bulk_operations.mixins import ListDestroyModelMixin, ListUpdateModelMixin
from rest_framework_extensions.settings import extensions_api_settings


class DetailSerializerMixin(object):
    """
    Add custom serializer for detail view
    """
    serializer_detail_class = None
    queryset_detail = None

    def get_serializer_class(self):
        error_message = "'{0}' should include a 'serializer_detail_class' attribute".format(self.__class__.__name__)
        assert self.serializer_detail_class is not None, error_message
        if self._is_request_to_detail_endpoint():
            return self.serializer_detail_class
        else:
            return super(DetailSerializerMixin, self).get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        if self._is_request_to_detail_endpoint() and self.queryset_detail is not None:
            return self.queryset_detail.all()  # todo: test all()
        else:
            return super(DetailSerializerMixin, self).get_queryset(*args, **kwargs)

    def _is_request_to_detail_endpoint(self):
        if hasattr(self, 'lookup_url_kwarg'):
            lookup = self.lookup_url_kwarg or self.lookup_field
        else: # DRF 2 compatibility
            lookup = self.pk_url_kwarg or self.slug_url_kwarg
        return lookup and lookup in self.kwargs


class PaginateByMaxMixin(object):
    def get_paginate_by(self, *args, **kwargs):
        if (get_rest_framework_features()['max_paginate_by'] and
            self.paginate_by_param and
            self.max_paginate_by and
            self.request.QUERY_PARAMS.get(self.paginate_by_param) == 'max'):
            return self.max_paginate_by
        else:
            return super(PaginateByMaxMixin, self).get_paginate_by(*args, **kwargs)


class ReadOnlyCacheResponseAndETAGMixin(ReadOnlyETAGMixin, CacheResponseMixin):
    pass


class CacheResponseAndETAGMixin(ETAGMixin, CacheResponseMixin):
    pass


class NestedViewSetMixin(object):
    def get_queryset(self):
        return self.filter_queryset_by_parents_lookups(
            super(NestedViewSetMixin, self).get_queryset()
        )

    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        if parents_query_dict:
            return queryset.filter(**parents_query_dict)
        else:
            return queryset

    def get_parents_query_dict(self):
        result = {}
        for kwarg_name in self.kwargs:
            if kwarg_name.startswith(extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX):
                query_lookup = kwarg_name.replace(
                    extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX,
                    '',
                    1
                )
                query_value = self.kwargs.get(kwarg_name)
                result[query_lookup] = query_value
        return result
