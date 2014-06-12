# -*- coding: utf-8 -*-
from django.test import TestCase

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework_extensions.routers import ExtendedDefaultRouter
from rest_framework_extensions.decorators import link, action
from rest_framework_extensions.compat_drf import add_trailing_slash_if_needed


class ExtendedDefaultRouterTest(TestCase):
    def setUp(self):
        self.router = ExtendedDefaultRouter()

    def get_routes_names(self, routes):
        return [i.name for i in routes]

    def get_dynamic_route_by_def_name(self, def_name, routes):
        try:
            return [i for i in routes if def_name in i.mapping.values()][0]
        except IndexError:
            return None

    def get_dynamic_routes_by_endpoint(self, endpoint, routes):
        try:
            return [i for i in routes if i.name == u'{basename}-%s' % endpoint]
        except IndexError:
            return None

    def test_dynamic_routes_should_be_first_in_order(self):
        class BasicViewSet(viewsets.ViewSet):
            def list(self, request, *args, **kwargs):
                return Response({'method': 'list'})

            @action()
            def action1(self, request, *args, **kwargs):
                return Response({'method': 'action1'})

            @link()
            def link1(self, request, *args, **kwargs):
                return Response({'method': 'link1'})

        routes = self.router.get_routes(BasicViewSet)
        expected = [
            '{basename}-action1',
            '{basename}-link1',
            '{basename}-list',
            '{basename}-detail'
        ]
        msg = '@action and @link methods should come first in routes order'
        self.assertEqual(self.get_routes_names(routes), expected, msg)

    def test_action_endpoint(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(endpoint='action-one')
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@action with endpoint route should map methods to endpoint if it is specified'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@action with endpoint route should use url with detail lookup'
        self.assertEqual(action1_route.url, add_trailing_slash_if_needed(u'^{prefix}/{lookup}/action-one/$'), msg)

    def test_link_endpoint(self):
        class BasicViewSet(viewsets.ViewSet):
            @link(endpoint='link-one')
            def link1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        link1_route = self.get_dynamic_route_by_def_name('link1', routes)

        msg = '@link with endpoint route should map methods to endpoint if it is specified'
        self.assertEqual(link1_route.mapping, {'get': 'link1'}, msg)

        msg = '@link with endpoint route should use url with detail lookup'
        self.assertEqual(link1_route.url, add_trailing_slash_if_needed(u'^{prefix}/{lookup}/link-one/$'), msg)

    def test_action__for_list(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(is_for_list=True)
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@action with is_for_list=True route should map methods to def name'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@action with is_for_list=True route should use url in list scope'
        self.assertEqual(action1_route.url, add_trailing_slash_if_needed(u'^{prefix}/action1/$'), msg)

    def test_action__for_list__and__with_endpoint(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(is_for_list=True, endpoint='action-one')
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@action with is_for_list=True and endpoint route should map methods to "endpoint"'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@action with is_for_list=True and endpoint route should use url in list scope with "endpoint" value'
        self.assertEqual(action1_route.url, add_trailing_slash_if_needed(u'^{prefix}/action-one/$'), msg)

    def test_actions__for_list_and_detail_with_exact_names(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(is_for_list=True, endpoint='action-one')
            def action1(self, request, *args, **kwargs):
                pass

            @action(endpoint='action-one')
            def action1_detail(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action1_detail_route = self.get_dynamic_route_by_def_name('action1_detail', routes)

        self.assertEqual(action1_list_route.mapping, {'post': 'action1'})
        self.assertEqual(action1_list_route.url, add_trailing_slash_if_needed(u'^{prefix}/action-one/$'))

        self.assertEqual(action1_detail_route.mapping, {'post': 'action1_detail'})
        self.assertEqual(action1_detail_route.url, add_trailing_slash_if_needed(u'^{prefix}/{lookup}/action-one/$'))

    def test_action_names(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(is_for_list=True)
            def action1(self, request, *args, **kwargs):
                pass

            @action()
            def action2(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action2_detail_route = self.get_dynamic_route_by_def_name('action2', routes)

        self.assertEqual(action1_list_route.name, u'{basename}-action1-list')
        self.assertEqual(action2_detail_route.name, u'{basename}-action2')

    def test_action_names__with_endpoints(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(is_for_list=True, endpoint='action_one')
            def action1(self, request, *args, **kwargs):
                pass

            @action(endpoint='action-two')
            def action2(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action2_detail_route = self.get_dynamic_route_by_def_name('action2', routes)

        self.assertEqual(action1_list_route.name, u'{basename}-action-one-list')
        self.assertEqual(action2_detail_route.name, u'{basename}-action-two')
        
    def test_action_and_link_with_same_endpoint(self):
        endpoint = 'test-endpoint'
        class BasicViewSet(viewsets.ViewSet):
            @link(endpoint=endpoint)
            def link1(self, request, *args, **kwargs):
                pass

            @action(methods=['POST', 'PUT'], endpoint=endpoint)
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        routes = self.get_dynamic_routes_by_endpoint(endpoint, routes)
        self.assertEqual(1, len(routes))
        route = routes[0]
        try:
            self.assertEqual('action1', route.mapping['post'])
        except KeyError:
            self.fail('Method "post" not found in route mapping')
        try:
            self.assertEqual('action1', route.mapping['put'])
        except KeyError:
            self.fail('Method "put" not found in route mapping')
        try:
            self.assertEqual('link1', route.mapping['get'])
        except KeyError:
            self.fail('Method "get" not found in route mapping')
