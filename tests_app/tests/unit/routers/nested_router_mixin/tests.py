from rest_framework.test import APITestCase
from rest_framework_extensions.routers import ExtendedSimpleRouter
from rest_framework_extensions.utils import compose_parent_pk_kwarg_name
from .views import (
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
    CustomRegexUserViewSet,
    CustomRegexGroupViewSet,
    CustomRegexPermissionViewSet,
)


def get_regex_pattern(urlpattern):
    return urlpattern.pattern.regex.pattern


class NestedRouterMixinTest(APITestCase):
    def get_lookup_regex(self, value):
        return '(?P<{0}>[^/.]+)'.format(value)

    def get_parent_lookup_regex(self, value):
        return '(?P<{0}>[^/.]+)'.format(compose_parent_pk_kwarg_name(value))

    def get_custom_regex_lookup(self, pk_kwarg_name, lookup_value_regex):
        """ Build lookup regex with custom regular expression. """
        return '(?P<{pk_kwarg_name}>{lookup_value_regex})'.format(
            pk_kwarg_name=pk_kwarg_name,
            lookup_value_regex=lookup_value_regex
        )

    def get_custom_regex_parent_lookup(self, parent_pk_kwarg_name,
                                       parent_lookup_value_regex):
        """ Build parent lookup regex with custom regular expression. """
        return self.get_custom_regex_lookup(
            compose_parent_pk_kwarg_name(parent_pk_kwarg_name),
            parent_lookup_value_regex
        )

    def test_one_route(self):
        router = ExtendedSimpleRouter()
        router.register(r'users', UserViewSet, 'user')

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(get_regex_pattern(router.urls[0]), r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(get_regex_pattern(router.urls[1]), r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

    def test_nested_route(self):
        router = ExtendedSimpleRouter()
        (
            router.register(r'users', UserViewSet, 'user')
                  .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user'])
        )

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(get_regex_pattern(router.urls[0]), r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(get_regex_pattern(router.urls[1]), r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

        # test users group list
        self.assertEqual(router.urls[2].name, 'users-group-list')
        self.assertEqual(get_regex_pattern(router.urls[2]), r'^users/{0}/groups/$'.format(
                self.get_parent_lookup_regex('user')
            )
        )

        # test users group detail
        self.assertEqual(router.urls[3].name, 'users-group-detail')
        self.assertEqual(get_regex_pattern(router.urls[3]), r'^users/{0}/groups/{1}/$'.format(
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
        self.assertEqual(get_regex_pattern(router.urls[0]), r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(get_regex_pattern(router.urls[1]), r'^users/{0}/$'.format(self.get_lookup_regex('pk')))

        # test users group list
        self.assertEqual(router.urls[2].name, 'users-group-list')
        self.assertEqual(get_regex_pattern(router.urls[2]), r'^users/{0}/groups/$'.format(
                self.get_parent_lookup_regex('user')
            )
        )

        # test users group detail
        self.assertEqual(router.urls[3].name, 'users-group-detail')
        self.assertEqual(get_regex_pattern(router.urls[3]), r'^users/{0}/groups/{1}/$'.format(
                self.get_parent_lookup_regex('user'),
                self.get_lookup_regex('pk')
            ),
        )

        # test users groups permission list
        self.assertEqual(router.urls[4].name, 'users-groups-permission-list')
        self.assertEqual(get_regex_pattern(router.urls[4]), r'^users/{0}/groups/{1}/permissions/$'.format(
                self.get_parent_lookup_regex('group__user'),
                self.get_parent_lookup_regex('group'),
            )
        )

        # test users groups permission detail
        self.assertEqual(router.urls[5].name, 'users-groups-permission-detail')
        self.assertEqual(get_regex_pattern(router.urls[5]), r'^users/{0}/groups/{1}/permissions/{2}/$'.format(
                self.get_parent_lookup_regex('group__user'),
                self.get_parent_lookup_regex('group'),
                self.get_lookup_regex('pk')
            ),
        )

    def test_nested_route_depth_3_custom_regex(self):
        """
        Nested routes with over two level of depth should respect all parents'
        `lookup_value_regex` attribute.
        """
        router = ExtendedSimpleRouter()
        (
            router.register(r'users', CustomRegexUserViewSet, 'user')
                  .register(r'groups', CustomRegexGroupViewSet, 'users-group',
                            parents_query_lookups=['user'])
                  .register(r'permissions', CustomRegexPermissionViewSet,
                            'users-groups-permission', parents_query_lookups=[
                               'group__user',
                               'group',
                            ]
                  )
        )

        # custom regex configuration
        user_viewset_regex = CustomRegexUserViewSet.lookup_value_regex
        group_viewset_regex = CustomRegexGroupViewSet.lookup_value_regex
        perm_viewset_regex = CustomRegexPermissionViewSet.lookup_value_regex

        # test user list
        self.assertEqual(router.urls[0].name, 'user-list')
        self.assertEqual(get_regex_pattern(router.urls[0]), r'^users/$')

        # test user detail
        self.assertEqual(router.urls[1].name, 'user-detail')
        self.assertEqual(get_regex_pattern(router.urls[1]), r'^users/{0}/$'.format(
            self.get_custom_regex_lookup('pk', user_viewset_regex))
        )

        # test users group list
        self.assertEqual(router.urls[2].name, 'users-group-list')
        self.assertEqual(get_regex_pattern(router.urls[2]), r'^users/{0}/groups/$'.format(
                self.get_custom_regex_parent_lookup('user', user_viewset_regex)
            )
        )
        # test users group detail
        self.assertEqual(router.urls[3].name, 'users-group-detail')
        self.assertEqual(get_regex_pattern(router.urls[3]), r'^users/{0}/groups/{1}/$'.format(
                self.get_custom_regex_parent_lookup('user', user_viewset_regex),
                self.get_custom_regex_lookup('pk', group_viewset_regex)
            ),
        )
        # test users groups permission list
        self.assertEqual(router.urls[4].name, 'users-groups-permission-list')
        self.assertEqual(get_regex_pattern(router.urls[4]), r'^users/{0}/groups/{1}/permissions/$'.format(
                self.get_custom_regex_parent_lookup('group__user', user_viewset_regex),
                self.get_custom_regex_parent_lookup('group', group_viewset_regex),
            )
        )

        # test users groups permission detail
        self.assertEqual(router.urls[5].name, 'users-groups-permission-detail')
        self.assertEqual(get_regex_pattern(router.urls[5]), r'^users/{0}/groups/{1}/permissions/{2}/$'.format(
                self.get_custom_regex_parent_lookup('group__user', user_viewset_regex),
                self.get_custom_regex_parent_lookup('group', group_viewset_regex),
                self.get_custom_regex_lookup('pk', perm_viewset_regex)
            ),
        )
