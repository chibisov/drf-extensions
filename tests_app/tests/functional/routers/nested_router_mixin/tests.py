from django.test import override_settings

from rest_framework.test import APITestCase

from .models import (
    NestedRouterMixinUserModel as UserModel,
    NestedRouterMixinGroupModel as GroupModel,
    NestedRouterMixinPermissionModel as PermissionModel,
    NestedRouterMixinTaskModel as TaskModel,
    NestedRouterMixinBookModel as BookModel,
    NestedRouterMixinCommentModel as CommentModel
)


@override_settings(ROOT_URLCONF='tests_app.tests.functional.routers.nested_router_mixin.urls')
class NestedRouterMixinTestBehaviourBase(APITestCase):

    def setUp(self):
        self.users = {
            'vova': UserModel.objects.create(id=1, name='vova'),
            'gena': UserModel.objects.create(id=2, name='gena'),
        }
        self.groups = {
            'users': GroupModel.objects.create(id=3, name='users'),
            'admins': GroupModel.objects.create(id=4, name='admins'),
            'super_admins': GroupModel.objects.create(id=5, name='super_admins'),
        }
        self.permissions = {
            'read': PermissionModel.objects.create(id=6, name='read'),
            'update': PermissionModel.objects.create(id=7, name='update'),
            'delete': PermissionModel.objects.create(id=8, name='delete'),
        }

        # add permissions to groups
        self.groups['users'].permissions.set([
            self.permissions['read']
        ])
        self.groups['admins'].permissions.set([
            self.permissions['read'],
            self.permissions['update'],
        ])
        self.groups['super_admins'].permissions.set([
            self.permissions['read'],
            self.permissions['update'],
            self.permissions['delete'],
        ])

        # add groups to users
        self.users['vova'].groups.set([
            self.groups['users']
        ])

        self.users['gena'].groups.set([
            self.groups['admins'],
            self.groups['super_admins'],
        ])


class NestedRouterMixinTestBehaviour__main_routes(NestedRouterMixinTestBehaviourBase):
    def test_users(self):
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.users['vova'].id,
                'name': self.users['vova'].name
            },
            {
                'id': self.users['gena'].id,
                'name': self.users['gena'].name
            },
        ]
        self.assertEqual(response.data, expected)

    def test_users_detail(self):
        url = '/users/{0}/'.format(self.users['gena'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'id': self.users['gena'].id,
            'name': self.users['gena'].name
        }
        self.assertEqual(response.data, expected)

    def test_users_groups(self):
        url = '/users/{0}/groups/'.format(self.users['gena'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.groups['admins'].id,
                'name': self.groups['admins'].name
            },
            {
                'id': self.groups['super_admins'].id,
                'name': self.groups['super_admins'].name
            }
        ]
        msg = 'Groups should be filtered by user'
        self.assertEqual(response.data, expected, msg=msg)

    def test_users_groups_detail(self):
        url = '/users/{user_pk}/groups/{group_pk}/'.format(
            user_pk=self.users['gena'].id,
            group_pk=self.groups['admins'].id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'id': self.groups['admins'].id,
            'name': self.groups['admins'].name
        }
        self.assertEqual(response.data, expected)

    def test_users_groups_detail__if_user_has_no_such_group(self):
        url = '/users/{user_pk}/groups/{group_pk}/'.format(
            user_pk=self.users['gena'].id,
            group_pk=self.groups['users'].id
        )
        response = self.client.get(url)
        msg = 'If user has no requested group it should return 404'
        self.assertEqual(response.status_code, 404, msg=msg)

    def test_simple_groups(self):
        response = self.client.get('/groups/')
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.groups['users'].id,
                'name': self.groups['users'].name
            },
            {
                'id': self.groups['admins'].id,
                'name': self.groups['admins'].name
            },
            {
                'id': self.groups['super_admins'].id,
                'name': self.groups['super_admins'].name
            },
        ]
        self.assertEqual(response.data, expected)

    def test_simple_permissions(self):
        response = self.client.get('/permissions/')
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.permissions['read'].id,
                'name': self.permissions['read'].name
            },
            {
                'id': self.permissions['update'].id,
                'name': self.permissions['update'].name
            },
            {
                'id': self.permissions['delete'].id,
                'name': self.permissions['delete'].name
            },
        ]
        self.assertEqual(response.data, expected)


class NestedRouterMixinTestBehaviour__register_on_one_depth(NestedRouterMixinTestBehaviourBase):
    def test_permissions(self):
        response = self.client.get('/permissions/')
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.permissions['read'].id,
                'name': self.permissions['read'].name
            },
            {
                'id': self.permissions['update'].id,
                'name': self.permissions['update'].name
            },
            {
                'id': self.permissions['delete'].id,
                'name': self.permissions['delete'].name
            },
        ]
        self.assertEqual(response.data, expected)

    def test_permissions_detail(self):
        url = '/permissions/{0}/'.format(self.permissions['read'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'id': self.permissions['read'].id,
            'name': self.permissions['read'].name
        }
        self.assertEqual(response.data, expected)

    def test_permissions_groups(self):
        url = '/permissions/{0}/groups/'.format(self.permissions['update'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.groups['admins'].id,
                'name': self.groups['admins'].name
            },
            {
                'id': self.groups['super_admins'].id,
                'name': self.groups['super_admins'].name
            },
        ]
        msg = 'Groups should be filtered by permission'
        self.assertEqual(response.data, expected, msg=msg)

    def test_permissions_users(self):
        url = '/permissions/{0}/users/'.format(self.permissions['delete'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.users['gena'].id,
                'name': self.users['gena'].name
            },
        ]
        msg = 'Users should be filtered by group permissions'
        self.assertEqual(response.data, expected, msg=msg)


class NestedRouterMixinTestBehaviour__actions_and_links(NestedRouterMixinTestBehaviourBase):
    def test_users_list_action(self):
        response = self.client.post('/users/users-list-action/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'users list action')

    def test_users_action(self):
        url = '/users/{0}/users-action/'.format(self.users['gena'].id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'users action')

    def test_groups_list_link(self):
        url = '/groups/groups-list-link/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'groups list link')

    def test_groups_link(self):
        url = '/groups/{0}/groups-link/'.format(
            self.groups['admins'].id,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'groups link')

    def test_users_groups_list_link(self):
        url = '/users/{0}/groups/groups-list-link/'.format(self.users['gena'].id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'groups list link')

    def test_permissions_list_action(self):
        url = '/permissions/permissions-list-action/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'permissions list action')

    def test_permissions_action(self):
        url = '/permissions/{0}/permissions-action/'.format(
            self.permissions['delete'].id,
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'permissions action')

    def test_users_groups_link(self):
        url = '/users/{0}/groups/{1}/groups-link/'.format(
            self.users['gena'].id,
            self.groups['admins'].id,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'groups link')

    def test_users_groups_permissions_list_action(self):
        url = '/users/{0}/groups/{1}/permissions/permissions-list-action/'.format(
            self.users['gena'].id,
            self.groups['admins'].id,
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'permissions list action')

    def test_users_groups_permissions_action(self):
        url = '/users/{0}/groups/{1}/permissions/{2}/permissions-action/'.format(
            self.users['gena'].id,
            self.groups['admins'].id,
            self.permissions['delete'].id,
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'permissions action')


@override_settings(ROOT_URLCONF='tests_app.tests.functional.routers.nested_router_mixin.urls_generic_relations')
class NestedRouterMixinTestBehaviour__generic_relations(APITestCase):

    def setUp(self):
        self.tasks = {
            'one': TaskModel.objects.create(id=1, title='Task one'),
            'two': TaskModel.objects.create(id=2, title='Task two'),
        }
        self.books = {
            'one': BookModel.objects.create(id=1, title='Book one'),
            'two': BookModel.objects.create(id=2, title='Book two'),
        }
        self.comments = {
            'for_task_one': CommentModel.objects.create(
                id=1,
                content_object=self.tasks['one'],
                text=u'Comment for task one'
            ),
            'for_task_two': CommentModel.objects.create(
                id=2,
                content_object=self.tasks['two'],
                text=u'Comment for task two'
            ),
            'for_book_one': CommentModel.objects.create(
                id=3,
                content_object=self.books['one'],
                text=u'Comment for book one'
            ),
            'for_book_two': CommentModel.objects.create(
                id=4,
                content_object=self.books['two'],
                text=u'Comment for book two'
            ),
        }

    def assertResult(self, response, result):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, result)

    def test_comments_for_tasks(self):
        url = '/tasks/{0}/comments/'.format(
            self.tasks['one'].id,
        )
        response = self.client.get(url)

        self.assertResult(response, [
            {
                'id': self.comments['for_task_one'].id,
                'content_type': self.comments['for_task_one'].content_type.id,
                'object_id': self.comments['for_task_one'].object_id,
                'text': self.comments['for_task_one'].text,
            }
        ])

        url = '/tasks/{0}/comments/'.format(
            self.tasks['two'].id,
        )
        response = self.client.get(url)
        self.assertResult(response, [
            {
                'id': self.comments['for_task_two'].id,
                'content_type': self.comments['for_task_two'].content_type.id,
                'object_id': self.comments['for_task_two'].object_id,
                'text': self.comments['for_task_two'].text,
            }
        ])

    def test_comments_for_books(self):
        url = '/books/{0}/comments/'.format(
            self.books['one'].id,
        )
        response = self.client.get(url)

        self.assertResult(response, [
            {
                'id': self.comments['for_book_one'].id,
                'content_type': self.comments['for_book_one'].content_type.id,
                'object_id': self.comments['for_book_one'].object_id,
                'text': self.comments['for_book_one'].text,
            }
        ])

        url = '/books/{0}/comments/'.format(
            self.books['two'].id,
        )
        response = self.client.get(url)
        self.assertResult(response, [
            {
                'id': self.comments['for_book_two'].id,
                'content_type': self.comments['for_book_two'].content_type.id,
                'object_id': self.comments['for_book_two'].object_id,
                'text': self.comments['for_book_two'].text,
            }
        ])


@override_settings(ROOT_URLCONF='tests_app.tests.functional.routers.nested_router_mixin.urls_parent_viewset_lookup')
class NestedRouterMixinTestBehaviour__parent_viewset_lookup(APITestCase):

    def setUp(self):
        self.users = {
            'vova': UserModel.objects.create(id=1, name='vova', email='vova@example.com'),
            'gena': UserModel.objects.create(id=2, name='gena', email='gena@example.com'),
        }
        self.groups = {
            'users': GroupModel.objects.create(id=3, name='users'),
            'admins': GroupModel.objects.create(id=4, name='admins'),
            'super_admins': GroupModel.objects.create(id=5, name='super_admins'),
        }

        # add groups to users
        self.users['vova'].groups.set([
            self.groups['users']
        ])

        self.users['gena'].groups.set([
            self.groups['admins'],
            self.groups['super_admins'],
        ])

    def test_users_detail(self):
        url = '/users/{0}/'.format(self.users['gena'].email)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'id': self.users['gena'].id,
            'name': self.users['gena'].name
        }
        self.assertEqual(response.data, expected)

    def test_users_groups(self):
        url = '/users/{0}/groups/'.format(self.users['gena'].email)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                'id': self.groups['admins'].id,
                'name': self.groups['admins'].name
            },
            {
                'id': self.groups['super_admins'].id,
                'name': self.groups['super_admins'].name
            }
        ]
        msg = 'Groups should be filtered by user'
        self.assertEqual(response.data, expected, msg=msg)

    def test_users_groups_detail(self):
        url = '/users/{user_email}/groups/{group_pk}/'.format(
            user_email=self.users['gena'].email,
            group_pk=self.groups['admins'].id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'id': self.groups['admins'].id,
            'name': self.groups['admins'].name
        }
        self.assertEqual(response.data, expected)

    def test_users_groups_detail__if_user_has_no_such_group(self):
        url = '/users/{user_email}/groups/{group_pk}/'.format(
            user_email=self.users['gena'].email,
            group_pk=self.groups['users'].id
        )
        response = self.client.get(url)
        msg = 'If user has no requested group it should return 404'
        self.assertEqual(response.status_code, 404, msg=msg)


# class NestedRouterMixinTestBehaviour__generic_relations1(APITestCase):
#     router = ExtendedSimpleRouter()
#     # tasks route
#     (
#         router.register(r'tasks', TaskViewSet)
#               .register(r'', TaskCommentViewSet, 'tasks-comment', parents_query_lookups=['object_id'])
#     )
#     # books route
#     (
#         router.register(r'books', BookViewSet)
#               .register(r'', BookCommentViewSet, 'books-comment', parents_query_lookups=['object_id'])
#     )
#
#     urls = router.urls
#
#     def setUp(self):
#         self.tasks = {
#             'one': TaskModel.objects.create(id=1, title='Task one'),
#             'two': TaskModel.objects.create(id=2, title='Task two'),
#         }
#         self.books = {
#             'one': BookModel.objects.create(id=1, title='Book one'),
#             'two': BookModel.objects.create(id=2, title='Book two'),
#         }
#         self.comments = {
#             'for_task_one': CommentModel.objects.create(
#                 id=1,
#                 content_object=self.tasks['one'],
#                 text=u'Comment for task one'
#             ),
#             'for_task_two': CommentModel.objects.create(
#                 id=2,
#                 content_object=self.tasks['two'],
#                 text=u'Comment for task two'
#             ),
#             'for_book_one': CommentModel.objects.create(
#                 id=3,
#                 content_object=self.books['one'],
#                 text=u'Comment for book one'
#             ),
#             'for_book_two': CommentModel.objects.create(
#                 id=4,
#                 content_object=self.books['two'],
#                 text=u'Comment for book two'
#             ),
#         }
#
#     def test_me(self):
#         print 'hell'
