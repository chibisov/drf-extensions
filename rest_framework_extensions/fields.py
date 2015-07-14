# -*- coding: utf-8 -*-
from rest_framework.fields import Field
from rest_framework.relations import HyperlinkedRelatedField


class ResourceUriField(HyperlinkedRelatedField):
    """
    Represents a hyperlinking uri that points to the detail view for that object.

    Example:
        class SurveySerializer(serializers.ModelSerializer):
            resource_uri = ResourceUriField(view_name='survey-detail')

            class Meta:
                model = Survey
                fields = ('id', 'resource_uri')

        ...
        {
            "id": 1,
            "resource_uri": "http://localhost/v1/surveys/1/",
        }
    """
    # todo: test me
    read_only = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('source', '*')
        super(ResourceUriField, self).__init__(*args, **kwargs)


class MappingField(Field):
    default_error_messages = {
        'key_not_found': '"{value}" not found in "mapping" keys',
        'value_not_found': '"{value}" not found in "mapping" values'
    }

    def __init__(self, mapping, reverse_mapping=None, **kwargs):
        super(MappingField, self).__init__(**kwargs)

        def check_dict(d):
            assert isinstance(d, dict), '"mapping" should be a dictionary'
            for k, v in d.items():
                assert isinstance(k, (str, int, bool)) and isinstance(v, (str, int, bool)), '"mapping" can contain only simple types'

        check_dict(mapping)

        self.mapping = mapping
        if reverse_mapping is None:
            self.reverse_mapping = {v: k for k, v in mapping.iteritems()}
        else:
            check_dict(reverse_mapping)
            self.reverse_mapping = reverse_mapping

    def to_representation(self, value):
        if value in self.mapping:
            return self.mapping[value]
        self.fail('key_not_found', value=value)

    def to_internal_value(self, data):
        if data in self.reverse_mapping:
            return self.reverse_mapping[data]
        self.fail('value_not_found', value=data)