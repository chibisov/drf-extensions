# -*- coding: utf-8 -*-
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework_extensions.fields import(
    NestedHyperlinkedRelatedField,
    NestedHyperlinkedIdentityField,
)
from rest_framework_extensions.compat import get_concrete_model
from rest_framework_extensions.utils import get_model_opts_concrete_fields, \
    get_rest_framework_features


def get_fields_for_partial_update(opts, init_data, fields, init_files=None):
    opts = get_concrete_model(opts.model)._meta
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


class NestedHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    """
    Extension of `HyperlinkedModelSerializer` that adds support for
    nested resources.
    """
    serializer_related_field = NestedHyperlinkedRelatedField
    serializer_url_field = NestedHyperlinkedIdentityField

    def get_default_field_names(self, declared_fields, model_info):
        """
        Return the default list of field names that will be used if the
        `Meta.fields` option is not specified.
        """
        return (
            [self.url_field_name] +
            list(declared_fields.keys()) +
            list(model_info.fields.keys()) +
            list(model_info.forward_relations.keys())
        )

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Create nested fields for forward and reverse relationships.
        """
        class NestedSerializer(NestedHyperlinkedModelSerializer):
            class Meta:
                model = relation_info.related_model
                depth = nested_depth - 1

        field_class = NestedSerializer
        field_kwargs = get_nested_relation_kwargs(relation_info)

        return field_class, field_kwargs
