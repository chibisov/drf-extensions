# -*- coding: utf-8 -*-
from rest_framework_extensions.utils import get_model_opts_concrete_fields


def get_fields_for_partial_update(opts, init_data, fields, init_files=None):
    opts = opts.model._meta.concrete_model._meta
    partial_fields = list((init_data or {}).keys()) + list((init_files or {}).keys())
    concrete_field_names = []
    for field in get_model_opts_concrete_fields(opts):
        if not field.primary_key:
            concrete_field_names.append(field.name)
            if field.name != field.attname:
                concrete_field_names.append(field.attname)
    update_fields = []
    for field_name in partial_fields:
        if field_name in fields:
            model_field_name = getattr(fields[field_name], 'source') or field_name
            if model_field_name in concrete_field_names:
                update_fields.append(model_field_name)
    return update_fields


class PartialUpdateSerializerMixin(object):
    def save(self, **kwargs):
        self._update_fields = kwargs.get('update_fields', None)
        return super(PartialUpdateSerializerMixin, self).save(**kwargs)

    def update(self, instance, validated_attrs):
        for attr, value in validated_attrs.items():
            if hasattr(getattr(instance, attr, None), 'set'):
                getattr(instance, attr).set(value)
            else:
                setattr(instance, attr, value)
        if self.partial and isinstance(instance, self.Meta.model):
            instance.save(
                update_fields=getattr(self, '_update_fields') or get_fields_for_partial_update(
                    opts=self.Meta,
                    init_data=self.get_initial(),
                    fields=self.fields.fields
                )
            )
        else:
            instance.save()
        return instance
