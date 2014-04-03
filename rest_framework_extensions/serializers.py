# -*- coding: utf-8 -*-


class PartialUpdateSerializerMixin(object):
    def save_object(self, obj, **kwargs):
        if self.partial and 'update_fields' not in kwargs:
            update_fields = list((self.init_data or {}).keys()) + list((self.init_files or {}).keys())
            update_fields = [i for i in update_fields if i in self.fields]
            kwargs['update_fields'] = update_fields

        return super(PartialUpdateSerializerMixin, self).save_object(obj, **kwargs)