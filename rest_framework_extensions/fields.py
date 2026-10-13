from rest_framework.relations import HyperlinkedRelatedField, SlugRelatedField
from django.db import models
from rest_framework.fields import Field

class ResourceUriField(HyperlinkedRelatedField):
    """
    Represents a hyperlinking uri that points to the
    detail view for that object.

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
        super().__init__(*args, **kwargs)


class SerializedRelatedField(SlugRelatedField):
    """
    A relational field that accepts a simple slug for writes
    (like SlugRelatedField), but expands to a nested serializer
    for reads if `serializer_class` is provided.

    Example:
        class OrderSerializer(serializers.ModelSerializer):
            address = SerializedRelatedField(
                serializer_class=AddressSerializer,
                queryset=Address.objects.all(),
                lookup_field="pk",
            )
    """

    def __init__(self, serializer_class=None, lookup_field="pk", **kwargs):
        self.serializer_class = serializer_class
        kwargs["slug_field"] = lookup_field
        super().__init__(**kwargs)

        if self.serializer_class is not None and self.queryset is None:
            raise AssertionError(
                "SerializedRelatedField with serializer_class requires a queryset"
            )

    def to_representation(self, value):
        # Ensure PKOnlyObject (used in select_related/prefetch) is resolved
        if hasattr(value, "pk") and not isinstance(value, models.Model):
            value = self.get_queryset().get(pk=value.pk)

        if self.serializer_class is not None:
            serializer = self.serializer_class(value, context=self.context)
            return serializer.data

        return super().to_representation(value)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return {
            super(SerializedRelatedField, self).to_representation(item): self.display_value(item) for item in queryset
        }


class FlexibleField(Field):
    """
    A field that allows independent read and write representations.

    Example:
        category = FlexibleField(
            read=serializers.SlugRelatedField(
                slug_field="slug",
                read_only=True,
            ),
            write=serializers.PrimaryKeyRelatedField(
                queryset=Category.objects.all(),
            ),
        )
    """

    def __init__(self, *, read=None, write=None, **kwargs):
        if read is None and write is None:
            raise AssertionError(
                "FlexibleField requires at least one of 'read' or 'write'."
            )

        self.read_field = read
        self.write_field = write

        if read is None:
            kwargs["write_only"] = True
        elif write is None:
            kwargs["read_only"] = True

        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        if self.read_field is not None:
            self.read_field.bind(field_name, self)

        if self.write_field is not None:
            self.write_field.bind(field_name, self)

    def to_representation(self, value):
        if self.read_field is None:
            raise AssertionError(
                "FlexibleField has no read field."
            )

        return self.read_field.to_representation(value)

    def to_internal_value(self, data):
        if self.write_field is None:
            raise AssertionError(
                "FlexibleField has no write field."
            )

        return self.write_field.run_validation(data)
