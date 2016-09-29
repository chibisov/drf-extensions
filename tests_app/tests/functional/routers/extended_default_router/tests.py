# -*- coding: utf-8 -*-
from django.core.urlresolvers import NoReverseMatch
from django.test import override_settings

from rest_framework_extensions.test import APITestCase


@override_settings(ROOT_URLCONF='tests_app.tests.functional.routers.extended_default_router.urls')
class ExtendedDefaultRouterTestBehaviour(APITestCase):

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
