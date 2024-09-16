from rest_framework import serializers
from rest_framework_extensions.fields import AsymmetricRelatedField

from .models import SomeModel, RelatedModel


class RelatedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedModel
        fields = ('id', 'name')


class SomeModelSerializer(serializers.ModelSerializer):
    related_model = AsymmetricRelatedField(
        serializer_class=RelatedModelSerializer,
        queryset=RelatedModel.objects.all()
    )

    class Meta:
        model = SomeModel
        fields = ('id', 'name', 'related_model')