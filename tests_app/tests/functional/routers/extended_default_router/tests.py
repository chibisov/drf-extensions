# -*- coding: utf-8 -*-
from django.core.urlresolvers import NoReverseMatch

from rest_framework_extensions.test import APITestCase
from rest_framework_extensions.routers import ExtendedDefaultRouter

from .views import (
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)


class ExtendedDefaultRouterTestBehaviour(APITestCase):
    router = ExtendedDefaultRouter()
    # nested routes
    (
        router.register(r'users', UserViewSet)
              .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user_groups'])
              .register(r'permissions', PermissionViewSet, 'users-groups-permission', parents_query_lookups=['group__user', 'group'])
    )
    # simple routes
    router.register(r'groups', GroupViewSet, 'group')
    router.register(r'permissions', PermissionViewSet, 'permission')

    urls = tuple(router.urls)

    def test_index_page(self):
        try:
            response = self.client.get('/')
        except NoReverseMatch:
            issue = 'https://github.com/chibisov/drf-extensions/issues/14'
            self.fail('DefaultRouter tries to reverse nested routes and breaks with error. NoReverseMatch should be '
                      'handled for nested routes. They must be excluded from index page. ' + issue)
        self.assertEqual(response.status_code, 200)

        expected = {
            'users': 'http://testserver/users/',
            'groups': 'http://testserver/groups/',
            'permissions': 'http://testserver/permissions/',
        }
        self.assertEqual(response.data, expected)