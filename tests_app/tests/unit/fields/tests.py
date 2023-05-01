from django.test import TestCase
from rest_framework import serializers
from .models import SomeModel, RelatedModel
from .serializers import SomeModelSerializer, RelatedModelSerializer
from rest_framework_extensions.fields import AsymmetricRelatedField


class TestAsymmetricRelatedField(TestCase):
    def setUp(self):
        self.related_model1 = RelatedModel.objects.create(name='related_model1')
        self.related_model2 = RelatedModel.objects.create(name='related_model2')
        self.some_model = SomeModel.objects.create(
            name='some_model', related_model=self.related_model1)

    def test_to_representation(self):
        field = AsymmetricRelatedField(serializer_class=RelatedModelSerializer)
        result = field.to_representation(self.related_model1)
        self.assertEqual(
            result, {'id': self.related_model1.id, 'name': 'related_model1'})

    def test_create(self):
        data = {
            'name': 'new_some_model',
            'related_model': self.related_model2.id
        }
        serializer = SomeModelSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertEqual(instance.name, 'new_some_model')
        self.assertEqual(instance.related_model, self.related_model2)

    def test_update(self):
        data = {
            'name': 'updated_some_model',
            'related_model': self.related_model2.id
        }
        serializer = SomeModelSerializer(
            instance=self.some_model, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertEqual(instance.name, 'updated_some_model')
        self.assertEqual(instance.related_model, self.related_model2)

    def test_read(self):
        serializer = SomeModelSerializer(instance=self.some_model)
        self.assertEqual(serializer.data, {
            'id': self.some_model.id,
            'name': 'some_model',
            'related_model': {
                'id': self.related_model1.id,
                'name': 'related_model1'
            }
        })
