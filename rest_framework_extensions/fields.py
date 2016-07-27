# -*- coding: utf-8 -*-
import functools
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch
from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from rest_framework.fields import get_attribute
from rest_framework.relations import (
    HyperlinkedRelatedField,
    HyperlinkedIdentityField,
)


class ResourceUriField(HyperlinkedIdentityField):
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
    pass


class NestedHyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    Handles HyperlinkedRelatedField with views that are nested.

    Args:
        view_name: Name of url rule used for reverse resolving
        lookup_map: Item specifig mapping how to resolve url kwargs for named url conf.
            If value is dict, it's used as is.
            If value is string, it's resolved to class using django import_string.
            If value is class (e.g. resolved from string above) lookup_map is constructed
            member variables `lookup_field`, `lookup_url_kwarg` and `parent_lookup_map`.
            If value is ommited, we try look for view from context and do above.
            If no value is resolvable by above means, error is raised.

    """
    def __init__(self, lookup_map=None, **kwargs):
        self.__lookup_map = lookup_map
        assert 'lookup_field' not in kwargs, "Do not use `lookup_field` use `lookup_map` instead."
        assert 'lookup_url_kwarg' not in kwargs, "Do not use `lookup_url_kwarg` use `lookup_map` instead."
        # FIXME: implement update operations with related fields
        kwargs['read_only'] = True
        kwargs['queryset'] = None
        super(NestedHyperlinkedRelatedField, self).__init__(**kwargs)

    @cached_property
    def _lookup_map(self):
        lookup_map = self.__lookup_map or self.context.get('view', None)

        assert lookup_map, (
            "Field `{field}` of type `{type}` in `{serializer}` requires `lookup_map` "
            "to be able to reverse `view_name`. \n"
            "You can pass that as argument or it can be resolved from view parameters. "
            "To resolve from view parameters, you need to pass view as argument "
            "(via `lookup_map` as string or reference) or in context by adding "
            "`context={{'view': view}}` when instantiating the serializer. ".format(
                field=self.field_name,
                type=self.__class__.__name__,
                serializer=self.parent.__class__.__name__,
            )
        )

        if isinstance(lookup_map, dict):
            return lookup_map

        if isinstance(lookup_map, six.string_types):
            lookup_map = import_string(lookup_map)

        lookup_field = getattr(lookup_map, 'lookup_field', None) or self.lookup_field
        lookup_url_kw = getattr(lookup_map, 'lookup_url_kwarg', None) or lookup_field
        parent_lookup_map = getattr(lookup_map, 'parent_lookup_map', {})
        map_ = {lookup_url_kw: lookup_field}
        map_.update(parent_lookup_map)
        return map_

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        # get lookup map (will use properties lookup_map and view)
        lookup_map = self._lookup_map
        get = lambda x: x(obj) if callable(x) else get_attribute(obj, x.split('.'))

        # build kwargs for reverse
        try:
            kwargs = dict((
                (key, get(source)) for (key, source) in lookup_map.items()
            ))
        except (KeyError, AttributeError) as exc:
            raise ValueError(
                "Got {exc_type} when attempting to create url for field "
                "`{field}` on serializer `{serializer}`. "
                "The serializer field lookup_map might be configured incorrectly. "
                "We used `{instance}` instance with lookup map `{lookup_map}`. "
                "Original exception text was: {exc}.".format(
                    exc_type=type(exc).__name__,
                    field=self.field_name,
                    serializer=self.parent.__class__.__name__,
                    instance=obj.__class__.__name__,
                    lookup_map=lookup_map,
                    exc=exc,
                )
            )

        try:
            return self.reverse(self.view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch as exc:
            raise ImproperlyConfigured(
                "Could not resolve URL for hyperlinked relationship in field "
                "`{field}` on serializer `{serializer}`. "
                "You may have failed to include the related model in your API, "
                "or incorrectly configured `view_name` or `lookup_map` "
                "attribute on this field. Original error: {exc}".format(
                    field=self.field_name,
                    view_name=self.view_name,
                    serializer=self.parent.__class__.__name__,
                    kwargs=kwargs,
                    exc=exc,
                )
            )


class NestedHyperlinkedIdentityField(NestedHyperlinkedRelatedField, HyperlinkedIdentityField):
    """
    Represents a nested hyperlinked resource itself.
    Will get lookup_map from view class in serializer context
    """
    pass
