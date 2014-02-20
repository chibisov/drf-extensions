# -*- coding: utf-8 -*-
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework_extensions.etag.mixins import ReadOnlyETAGMixin, ETAGMixin
from rest_framework_extensions.utils import get_rest_framework_features


class DetailSerializerMixin(object):
    """
    Add custom serializer for detail view
    """
    serializer_detail_class = None
    queryset_detail = None

    def get_serializer_class(self):
        error_message = "'{0}' should include a 'serializer_detail_class' attribute".format(self.__class__.__name__)
        assert self.serializer_detail_class is not None, error_message
        if getattr(self, 'object', None):
            return self.serializer_detail_class
        else:
            return super(DetailSerializerMixin, self).get_serializer_class()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset(is_for_detail=True))
        return super(DetailSerializerMixin, self).get_object(queryset=queryset)

    def get_queryset(self, is_for_detail=False):
        if self.queryset_detail is not None and is_for_detail:
            return self.queryset_detail._clone()  # todo: test _clone()
        else:
            return super(DetailSerializerMixin, self).get_queryset()


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