# -*- coding: utf-8 -*-
from django.db import models

from rest_framework_extensions.compat import get_concrete_model
from rest_framework_extensions.utils import get_model_opts_concrete_fields


class PartialUpdateSerializerMixin(object):
    def save_object(self, obj, **kwargs):
        if self.partial and 'update_fields' not in kwargs and isinstance(obj, self.opts.model):
            kwargs['update_fields'] = self._get_fields_for_partial_update()

        return super(PartialUpdateSerializerMixin, self).save_object(obj, **kwargs)

    def _get_fields_for_partial_update(self):
        cls = self.opts.model
        opts = get_concrete_model(cls)._meta
        partial_fields = list((self.init_data or {}).keys()) + list((self.init_files or {}).keys())
        concrete_field_names = [i.name for i in get_model_opts_concrete_fields(opts)]
        update_fields = []
        for field_name in partial_fields:
            if field_name in self.fields:
                model_field_name = getattr(self.fields[field_name], 'source') or field_name
                if model_field_name in concrete_field_names:
                    update_fields.append(model_field_name)
        return update_fields