# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.files import File

from rest_framework_extensions.compat import BytesIO

from .serializers import CommentSerializer
from .models import UserModel, CommentModel


class PartialUpdateSerializerMixinTest(TestCase):
    def setUp(self):
        self.files = [
            File(BytesIO(u'file one'.encode('utf-8')), name='file1.txt'),
            File(BytesIO(u'file two'.encode('utf-8')), name='file2.txt'),
        ]
        self.files[0]._set_size(8)
        self.files[1]._set_size(8)
        self.user = UserModel.objects.create(name='gena')
        self.comment = CommentModel.objects.create(
            user=self.user,
            title='hello',
            text='world',
            attachment=self.files[0]
        )

    def get_comment(self):
        return CommentModel.objects.get(pk=self.comment.pk)

    def test_should_use_default_saving_without_partial(self):
        serializer = CommentSerializer(data={
            'user': self.user.id,
            'title': 'hola',
            'text': 'amigos'
        })
        self.assertTrue(serializer.is_valid())
        saved_object = serializer.save()
        self.assertEqual(saved_object.user, self.user)
        self.assertEqual(saved_object.title, 'hola')
        self.assertEqual(saved_object.text, 'amigos')

    def test_should_save_partial(self):
        serializer = CommentSerializer(instance=self.comment, data={'title': 'hola'}, partial=True)
        self.assertTrue(serializer.is_valid())
        saved_object = serializer.save()
        self.assertEqual(saved_object.user, self.user)
        self.assertEqual(saved_object.title, 'hola')
        self.assertEqual(saved_object.text, 'world')

    def test_should_save_only_fields_from_data_for_partial_update(self):
        # it's important to use different instances for Comment, because serializer's save method affects
        # instance from arguments
        serializer_one = CommentSerializer(instance=self.get_comment(), data={'title': 'goodbye'}, partial=True)
        serializer_two = CommentSerializer(instance=self.get_comment(), data={'text': 'moon'}, partial=True)
        serializer_three = CommentSerializer(instance=self.get_comment(),
                                             data={},
                                             files={'attachment': self.files[1]},
                                             partial=True)
        self.assertTrue(serializer_one.is_valid())
        self.assertTrue(serializer_two.is_valid())
        self.assertTrue(serializer_three.is_valid())
        serializer_one.save()
        serializer_two.save()
        serializer_three.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.attachment.read(), u'file two'.encode('utf-8'))
        self.assertEqual(fresh_instance.text, 'moon')
        self.assertEqual(fresh_instance.title, 'goodbye')

    def test_should_not_try_to_update_fields_that_are_not_in_model(self):
        data = {
            'title': 'goodbye',
            'not_existing_field': 'moon'
        }
        serializer = CommentSerializer(instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        try:
            serializer.save()
        except ValueError:
            msg = 'Should not pass values to update_fields from data, if they are not in model'
            self.fail(msg)
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')
        self.assertEqual(fresh_instance.text, 'world')

    def test_should_not_try_to_update_fields_that_are_not_allowed_from_serializer(self):
        data = {
            'title': 'goodbye',
            'hidden_text': 'do not change me'
        }
        serializer = CommentSerializer(instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')
        self.assertEqual(fresh_instance.text, 'world')
        self.assertEqual(fresh_instance.hidden_text, None)

    def test_should_use_list_of_fields_to_update_from_arguments_if_it_passed(self):
        data = {
            'title': 'goodbye',
            'text': 'moon'
        }
        serializer = CommentSerializer(instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save(**{'update_fields': ['title']})
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')
        self.assertEqual(fresh_instance.text, 'world')