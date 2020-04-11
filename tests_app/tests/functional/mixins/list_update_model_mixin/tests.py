import json

import unittest

import django
from django.test import override_settings

from rest_framework.test import APITestCase
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework_extensions import utils

from .models import (
    CommentForListUpdateModelMixin as Comment,
    UserForListUpdateModelMixin as User
)
from tests_app.testutils import override_extensions_api_settings


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.list_update_model_mixin.urls')
class ListUpdateModelMixinTest(APITestCase):

    def setUp(self):
        self.comments = [
            Comment.objects.create(
                id=1,
                email='example@ya.ru'
            ),
            Comment.objects.create(
                id=2,
                email='example@gmail.com'
            )
        ]
        self.protection_headers = {
            utils.prepare_header_name(extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME): 'true'
        }
        self.patch_data = {
            'email': 'example@yandex.ru'
        }

    def test_simple_response(self):
        resp = self.client.get('/comments/')
        expected = [
            {
                'id': 1,
                'email': 'example@ya.ru'
            },
            {
                'id': 2,
                'email': 'example@gmail.com'
            }
        ]
        self.assertEqual(resp.data, expected)

    def test_filter_works(self):
        resp = self.client.get('/comments/?id=1')
        expected = [
            {
                'id': 1,
                'email': 'example@ya.ru'
            }
        ]
        self.assertEqual(resp.data, expected)

    def test_update_instance(self):
        data = {
            'id': 1,
            'email': 'example@yandex.ru'
        }
        resp = self.client.put('/comments/1/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Comment.objects.get(pk=1).email, 'example@yandex.ru')

    def test_partial_update_instance(self):
        data = {
            'id': 1,
            'email': 'example@yandex.ru'
        }
        resp = self.client.patch('/comments/1/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Comment.objects.get(pk=1).email, 'example@yandex.ru')

    def test_bulk_partial_update__without_protection_header(self):
        resp = self.client.patch('/comments/', data=json.dumps(self.patch_data), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        expected_message = {
            'detail': 'Header \'{0}\' should be provided for bulk operation.'.format(
                extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME
            )
        }
        self.assertEqual(resp.data, expected_message)

    def test_bulk_partial_update__with_protection_header(self):
        resp = self.client.patch('/comments/', data=json.dumps(self.patch_data), content_type='application/json', **self.protection_headers)
        self.assertEqual(resp.status_code, 204)
        for comment in Comment.objects.all():
            self.assertEqual(comment.email, self.patch_data['email'])

    @override_extensions_api_settings(DEFAULT_BULK_OPERATION_HEADER_NAME=None)
    def test_bulk_partial_update__without_protection_header__and_with_turned_off_protection_header(self):
        resp = self.client.patch('/comments/', data=json.dumps(self.patch_data), content_type='application/json', **self.protection_headers)
        self.assertEqual(resp.status_code, 204)
        for comment in Comment.objects.all():
            self.assertEqual(comment.email, self.patch_data['email'])

    def test_bulk_partial_update__should_update_filtered_queryset(self):
        resp = self.client.patch('/comments/?id=1', data=json.dumps(self.patch_data), content_type='application/json', **self.protection_headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Comment.objects.get(pk=1).email, self.patch_data['email'])
        self.assertEqual(Comment.objects.get(pk=2).email, self.comments[1].email)

    def test_bulk_partial_update__should_not_update_if_client_has_no_permissions(self):
        resp = self.client.patch('/comments-with-permission/', data=json.dumps(self.patch_data), content_type='application/json', **self.protection_headers)
        self.assertEqual(resp.status_code, 404)
        for i, comment in enumerate(Comment.objects.all()):
            self.assertEqual(comment.email, self.comments[i].email)


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.list_update_model_mixin.urls')
class ListUpdateModelMixinTestBehaviour__serializer_fields(APITestCase):

    def setUp(self):
        self.user = User.objects.create(
            id=1,
            name='Gennady',
            age=24,
            last_name='Chibisov',
            email='example@ya.ru',
            password='somepassword'
        )
        self.headers = {
            utils.prepare_header_name(extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME): 'true'
        }

    def get_fresh_user(self):
        return User.objects.get(pk=self.user.pk)

    def test_simple_response(self):
        resp = self.client.get('/users/')
        expected = [
            {
                'id': 1,
                'age': 24,
                'name': 'Gennady',
                'surname': 'Chibisov'
            }
        ]
        self.assertEqual(resp.data, expected)

    def test_invalid_for_db_data(self):
        data = {
            'age': 'Not integer value'
        }
        try:
            resp = self.client.patch('/users/', data=json.dumps(data), content_type='application/json', **self.headers)
        except ValueError:
            self.fail('Errors with invalid for DB data should be caught')
        else:
            self.assertEqual(resp.status_code, 400)
            if django.VERSION < (3, 0, 0):
                expected_message = {
                    'detail': "invalid literal for int() with base 10: 'Not integer value'"
                }
            else:
                expected_message = {
                    'detail': "Field 'age' expected a number but got 'Not integer value'."
                }
            self.assertEqual(resp.data, expected_message)

    def test_should_use_source_if_it_set_in_serializer(self):
        data = {
            'surname': 'Ivanov'
        }
        resp = self.client.patch('/users/', data=json.dumps(data), content_type='application/json', **self.headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self.get_fresh_user().last_name, data['surname'])

    def test_should_update_write_only_fields(self):
        data = {
            'password': '123'
        }
        resp = self.client.patch('/users/', data=json.dumps(data), content_type='application/json', **self.headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self.get_fresh_user().password, data['password'])

    def test_should_not_update_read_only_fields(self):
        data = {
            'name': 'Ivan'
        }
        resp = self.client.patch('/users/', data=json.dumps(data), content_type='application/json', **self.headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self.get_fresh_user().name, self.user.name)

    def test_should_not_update_hidden_fields(self):
        data = {
            'email': 'example@gmail.com'
        }
        resp = self.client.patch('/users/', data=json.dumps(data), content_type='application/json', **self.headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self.get_fresh_user().email, self.user.email)
