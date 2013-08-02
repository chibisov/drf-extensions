# -*- coding: utf-8 -*-


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