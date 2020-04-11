import json

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from tests_app.testutils import basic_auth_header
from .models import PermissionsComment


class ExtendedDjangoObjectPermissionTestMixin:
    def setUp(self):
        from guardian.shortcuts import assign_perm

        # create users
        create = User.objects.create_user
        users = {
            'fullaccess': create('fullaccess', 'fullaccess@example.com', 'password'),
            'readonly': create('readonly', 'readonly@example.com', 'password'),
            'writeonly': create('writeonly', 'writeonly@example.com', 'password'),
            'deleteonly': create('deleteonly', 'deleteonly@example.com', 'password'),
        }

        # create custom permission
        Permission.objects.get_or_create(
            codename='view_permissionscomment',
            content_type=ContentType.objects.get_for_model(PermissionsComment),
            defaults={'name': 'Can view comment'},
        )

        # give everyone model level permissions, as we are not testing those
        everyone = Group.objects.create(name='everyone')
        model_name = PermissionsComment._meta.model_name
        app_label = PermissionsComment._meta.app_label
        f = '{0}_{1}'.format
        perms = {
            'view': f('view', model_name),
            'change': f('change', model_name),
            'delete': f('delete', model_name)
        }
        for perm in perms.values():
            perm = '{0}.{1}'.format(app_label, perm)
            assign_perm(perm, everyone)
        everyone.user_set.add(*users.values())

        # appropriate object level permissions
        readers = Group.objects.create(name='readers')
        writers = Group.objects.create(name='writers')
        deleters = Group.objects.create(name='deleters')

        model = PermissionsComment.objects.create(text='foo', id=1)

        assign_perm(perms['view'], readers, model)
        assign_perm(perms['change'], writers, model)
        assign_perm(perms['delete'], deleters, model)

        readers.user_set.add(users['fullaccess'], users['readonly'])
        writers.user_set.add(users['fullaccess'], users['writeonly'])
        deleters.user_set.add(users['fullaccess'], users['deleteonly'])

        self.credentials = {}
        for user in users.values():
            self.credentials[user.username] = basic_auth_header(user.username, 'password')


@override_settings(ROOT_URLCONF='tests_app.tests.functional.permissions.extended_django_object_permissions.urls')
class ExtendedDjangoObjectPermissionsTest_should_inherit_standard(ExtendedDjangoObjectPermissionTestMixin,
                                                                  APITestCase):

    # Delete
    def test_can_delete_permissions(self):
        response = self.client.delete(
            '/comments/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['deleteonly']})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_permissions(self):
        response = self.client.delete(
            '/comments/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Update
    def test_can_update_permissions(self):
        response = self.client.patch(
            '/comments/1/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['writeonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), 'foobar')

    def test_cannot_update_permissions(self):
        response = self.client.patch(
            '/comments/1/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['deleteonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_permissions_non_existing(self):
        response = self.client.patch(
            '/comments/999/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['deleteonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Read
    def test_can_read_permissions(self):
        response = self.client.get(
            '/comments/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_read_permissions(self):
        response = self.client.get(
            '/comments/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['writeonly']})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Read list
    def test_can_read_list_permissions(self):
        response = self.client.get(
            '/comments-permission-filter-backend/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id'), 1)

    def test_cannot_read_list_permissions(self):
        response = self.client.get(
            '/comments-permission-filter-backend/',
            **{'HTTP_AUTHORIZATION': self.credentials['writeonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])


@override_settings(ROOT_URLCONF='tests_app.tests.functional.permissions.extended_django_object_permissions.urls')
class ExtendedDjangoObjectPermissionsTest_without_hiding_forbidden_objects(ExtendedDjangoObjectPermissionTestMixin,
                                                                           APITestCase):

    # Delete
    def test_can_delete_permissions(self):
        response = self.client.delete(
            '/comments-without-hiding-forbidden-objects/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['deleteonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_permissions(self):
        response = self.client.delete(
            '/comments-without-hiding-forbidden-objects/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Update
    def test_can_update_permissions(self):
        response = self.client.patch(
            '/comments-without-hiding-forbidden-objects/1/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['writeonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), 'foobar')

    def test_cannot_update_permissions(self):
        response = self.client.patch(
            '/comments-without-hiding-forbidden-objects/1/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['deleteonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_update_permissions_non_existing(self):
        response = self.client.patch(
            '/comments-without-hiding-forbidden-objects/999/',
            content_type='application/json',
            data=json.dumps({'text': 'foobar'}),
            **{
                'HTTP_AUTHORIZATION': self.credentials['deleteonly']
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Read
    def test_can_read_permissions(self):
        response = self.client.get(
            '/comments-without-hiding-forbidden-objects/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_read_permissions(self):
        response = self.client.get(
            '/comments-without-hiding-forbidden-objects/1/',
            **{'HTTP_AUTHORIZATION': self.credentials['writeonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Read list
    def test_can_read_list_permissions(self):
        response = self.client.get(
            '/comments-without-hiding-forbidden-objects-permission-filter-backend/',
            **{'HTTP_AUTHORIZATION': self.credentials['readonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id'), 1)

    def test_cannot_read_list_permissions(self):
        response = self.client.get(
            '/comments-without-hiding-forbidden-objects-permission-filter-backend/',
            **{'HTTP_AUTHORIZATION': self.credentials['writeonly']}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])
