from django.test import TestCase
from django.core.files.base import ContentFile
from rest_framework_extensions.serializers import get_fields_for_partial_update

from .serializers import CommentSerializer, UserSerializer, \
    CommentSerializerWithGroupedFields, CommentSerializerWithAllowedUserId
from .models import UserModel, CommentModel


class PartialUpdateSerializerMixinTest(TestCase):
    def setUp(self):
        self.files = [
            ContentFile(u'file one'.encode('utf-8'), name='file1.txt'),
            ContentFile(u'file two'.encode('utf-8'), name='file2.txt'),
        ]
        self.files[0].size = 8
        self.files[1].size = 8
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
            'text': 'amigos',
        })

        self.assertTrue(serializer.is_valid())  # bug for python3 comes from here

        saved_object = serializer.save()
        self.assertEqual(saved_object.user, self.user)
        self.assertEqual(saved_object.title, 'hola')
        self.assertEqual(saved_object.text, 'amigos')

    def test_should_save_partial(self):
        serializer = CommentSerializer(
            instance=self.comment, data={'title': 'hola'}, partial=True)
        self.assertTrue(serializer.is_valid())
        saved_object = serializer.save()
        self.assertEqual(saved_object.user, self.user)
        self.assertEqual(saved_object.title, 'hola')
        self.assertEqual(saved_object.text, 'world')

    def test_update_fields_correctly_determined(self):
        serializer = CommentSerializerWithGroupedFields(
            instance=self.comment,
            data={'text_content': {'title': 'hola', 'text': 'group'},
                  'title_from_source': 'hola', 'attachment': self.files[1]},
            partial=True)
        update_fields = get_fields_for_partial_update(
            serializer.Meta,
            serializer.get_initial(),
            serializer.fields.fields)
        self.assertListEqual(update_fields, ['attachment', 'text', 'title'])

    def test_should_save_grouped_partial(self):
        serializer = CommentSerializerWithGroupedFields(
            instance=self.comment,
            data={'text_content': {'title': 'hola', 'text': 'group'}},
            partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.title, 'hola')
        self.assertEqual(self.comment.text, 'group')

    def test_should_save_only_fields_from_data_for_partial_update(self):
        # it's important to use different instances for Comment,
        # because serializer's save method affects instance from arguments
        serializer_one = CommentSerializer(
            instance=self.get_comment(),
            data={'title': 'goodbye'}, partial=True)
        serializer_two = CommentSerializer(
            instance=self.get_comment(), data={'text': 'moon'}, partial=True)
        serializer_three_kwargs = {
            'instance': self.get_comment(),
            'partial': True
        }
        serializer_three_kwargs['data'] = {'attachment': self.files[1]}
        serializer_three = CommentSerializer(**serializer_three_kwargs)
        self.assertTrue(serializer_one.is_valid())
        self.assertTrue(serializer_two.is_valid())
        self.assertTrue(serializer_three.is_valid())

        # saving three serializers expecting they don't affect each other's saving
        serializer_one.save()
        serializer_two.save()
        serializer_three.save()

        fresh_instance = self.get_comment()

        self.assertEqual(fresh_instance.attachment.read(), u'file two'.encode('utf-8'))
        fresh_instance.attachment.close()

        self.assertEqual(fresh_instance.text, 'moon')
        self.assertEqual(fresh_instance.title, 'goodbye')

    def test_should_use_related_field_name_for_update_field_list(self):
        another_user = UserModel.objects.create(name='vova')
        data = {
            'title': 'goodbye',
            'user': another_user.pk
        }
        serializer = CommentSerializer(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')
        self.assertEqual(fresh_instance.user, another_user)

    def test_should_use_field_source_value_for_searching_model_concrete_fields(self):
        data = {
            'title_from_source': 'goodbye'
        }
        serializer = CommentSerializer(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')

    def test_should_not_use_m2m_field_name_for_update_field_list(self):
        another_user = UserModel.objects.create(name='vova')
        data = {
            'title': 'goodbye',
            'users_liked': [self.user.pk, another_user.pk]
        }
        serializer = CommentSerializer(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        try:
            serializer.save()
        except ValueError:
            self.fail(
                'If m2m field used in partial update then it should not be used in update_fields list')
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.title, 'goodbye')
        users_liked = set(
            fresh_instance.users_liked.all().values_list('pk', flat=True))
        self.assertEqual(
            users_liked, set([self.user.pk, another_user.pk]))

    def test_should_not_use_related_set_field_name_for_update_field_list(self):
        another_user = UserModel.objects.create(name='vova')
        another_comment = CommentModel.objects.create(
            user=another_user,
            title='goodbye',
            text='moon',
        )
        data = {
            'name': 'vova',
            'comments': [another_comment.pk]
        }
        serializer = UserSerializer(instance=another_user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        try:
            serializer.save()
        except ValueError:
            self.fail('If related set field used in partial update then it should not be used in update_fields list')
        fresh_comment = CommentModel.objects.get(pk=another_comment.pk)
        fresh_user = UserModel.objects.get(pk=another_user.pk)
        self.assertEqual(fresh_comment.user, another_user)
        self.assertEqual(fresh_user.name, 'vova')

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

    def test_should_not_use_field_attname_for_update_fields__if_attname_not_allowed_in_serializer_fields(self):
        another_user = UserModel.objects.create(name='vova')
        data = {
            'title': 'goodbye',
            'user_id': another_user.id
        }
        serializer = CommentSerializer(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.user_id, self.user.id)

    def test_should_use_field_attname_for_update_fields__if_attname_allowed_in_serializer_fields(self):
        another_user = UserModel.objects.create(name='vova')
        data = {
            'title': 'goodbye',
            'user_id': another_user.id
        }
        serializer = CommentSerializerWithAllowedUserId(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.user_id, another_user.id)

    def test_should_not_use_pk_field_for_update_fields(self):
        old_pk = self.get_comment().pk
        data = {
            'id': old_pk + 1,
            'title': 'goodbye'
        }
        serializer = CommentSerializer(
            instance=self.get_comment(), data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        try:
            serializer.save()
        except ValueError:
            self.fail(
                'Primary key field should be excluded from update_fields list')
        fresh_instance = self.get_comment()
        self.assertEqual(fresh_instance.pk, old_pk)
        self.assertEqual(fresh_instance.title, u'goodbye')
