# -*- coding: utf-8 -*-


class DetailSerializerMixin(object):
    """
    Add custom serializer for detail view
    """
    serializer_detail_class = None

    def get_serializer_class(self):
        error_message = "'{0}' should include a 'serializer_detail_class' attribute".format(self.__class__.__name__)
        assert self.serializer_detail_class is not None, error_message
        if getattr(self, 'object', None):
            return self.serializer_detail_class
        else:
            return super(DetailSerializerMixin, self).get_serializer_class()