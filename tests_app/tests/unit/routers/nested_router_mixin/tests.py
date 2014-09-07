# -*- coding: utf-8 -*-
from rest_framework_extensions.compat_drf import get_lookup_allowed_symbols
from rest_framework_extensions.test import APITestCase
from rest_framework_extensions.routers import ExtendedSimpleRouter
from rest_framework_extensions.utils import compose_parent_pk_kwarg_name
from .views import (
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)


class NestedRouterMixinTest(APITestCase):
    def get_lookup_regex(self, value):
        return get_lookup_allowed_symbols(value)
        # return '(?P<{0}>[^/]+)'.format(value)

    def get_parent_lookup_regex(self, value):
        return get_lookup_allowed_symbols(compose_parent_pk_kwarg_name(value), force_dot=True)
        # return '(?P<{0}>[^/.]+)'.format(compose_parent_pk_kwarg_name(value))

    def test_one_route(self):
        router = ExtendedSimpleRouter()
        router.register(r'users', UserViewSet, 'user')

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(router.urls[0]._regex, r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(router.urls[1]._regex, r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

    def test_nested_route(self):
        router = ExtendedSimpleRouter()
        (
            router.register(r'users', UserViewSet, 'user')
                  .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user'])
        )

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(router.urls[0]._regex, r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(router.urls[1]._regex, r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

        # test users group list
        self.assertEqual(router.urls[2].name, 'users-group-list')
        self.assertEqual(router.urls[2]._regex, r'^users/{0}/groups/$'.format(
                self.get_parent_lookup_regex('user')
            )
        )

        # test users group detail
        self.assertEqual(router.urls[3].name, 'users-group-detail')
        self.assertEqual(router.urls[3]._regex, r'^users/{0}/groups/{1}/$'.format(
                self.get_parent_lookup_regex('user'),
                self.get_lookup_regex('pk')
            ),
        )

    def test_nested_route_depth_3(self):
        router = ExtendedSimpleRouter()
        (
            router.register(r'users', UserViewSet, 'user')
                  .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user'])
                  .register(r'permissions', PermissionViewSet, 'users-groups-permission', parents_query_lookups=[
                               'group__user',
                               'group',
                            ]
                  )
        )

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(router.urls[0]._regex, r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(router.urls[1]._regex, r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

        # test users group list
        self.assertEqual(router.urls[2].name, 'users-group-list')
        self.assertEqual(router.urls[2]._regex, r'^users/{0}/groups/$'.format(
                self.get_parent_lookup_regex('user')
            )
        )

        # test users group detail
        self.assertEqual(router.urls[3].name, 'users-group-detail')
        self.assertEqual(router.urls[3]._regex, r'^users/{0}/groups/{1}/$'.format(
                self.get_parent_lookup_regex('user'),
                self.get_lookup_regex('pk')
            ),
        )

        # test users groups permission list
        self.assertEqual(router.urls[4].name, 'users-groups-permission-list')
        self.assertEqual(router.urls[4]._regex, r'^users/{0}/groups/{1}/permissions/$'.format(
                self.get_parent_lookup_regex('group__user'),
                self.get_parent_lookup_regex('group'),
            )
        )

        # test users groups permission detail
        self.assertEqual(router.urls[5].name, 'users-groups-permission-detail')
        self.assertEqual(router.urls[5]._regex, r'^users/{0}/groups/{1}/permissions/{2}/$'.format(
                self.get_parent_lookup_regex('group__user'),
                self.get_parent_lookup_regex('group'),
                self.get_lookup_regex('pk')
            ),
        )