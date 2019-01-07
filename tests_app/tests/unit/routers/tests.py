from django.test import TestCase

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.routers import ExtendedDefaultRouter


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

    def test_dynamic_list_route_should_come_before_detail_route(self):
        class BasicViewSet(viewsets.ViewSet):
            def list(self, request, *args, **kwargs):
                return Response({'method': 'list'})

            @action(detail=False)
            def detail1(self, request, *args, **kwargs):
                return Response({'method': 'detail1'})

        routes = self.router.get_routes(BasicViewSet)
        expected = [
            '{basename}-list',
            '{basename}-detail1',
            '{basename}-detail'
        ]
        msg = '@detail_route methods should come first in routes order'
        self.assertEqual(self.get_routes_names(routes), expected, msg)

    def test_detail_route(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=True)
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@detail_route should map methods to def name'
        self.assertEqual(action1_route.mapping, {'get': 'action1'}, msg)

        msg = '@detail_route should use url with detail lookup'
        self.assertEqual(action1_route.url, u'^{prefix}/{lookup}/action1{trailing_slash}$', msg)

    def test_detail_route__with_methods(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=True, methods=['post'])
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@detail_route should map methods to def name'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@detail_route should use url with detail lookup'
        self.assertEqual(action1_route.url, u'^{prefix}/{lookup}/action1{trailing_slash}$', msg)

    def test_detail_route__with_methods__and__with_url_path(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=True, methods=['post'], url_path='action-one')
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@detail_route should map methods to "url_path"'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@detail_route should use url with detail lookup and "url_path" value'
        self.assertEqual(action1_route.url, u'^{prefix}/{lookup}/action-one{trailing_slash}$', msg)

    def test_list_route(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False)
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@list_route should map methods to def name'
        self.assertEqual(action1_route.mapping, {'get': 'action1'}, msg)

        msg = '@list_route should use url in list scope'
        self.assertEqual(action1_route.url, u'^{prefix}/action1{trailing_slash}$', msg)

    def test_list_route__with_methods(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False, methods=['post'])
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@list_route should map methods to def name'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@list_route should use url in list scope'
        self.assertEqual(action1_route.url, u'^{prefix}/action1{trailing_slash}$', msg)

    def test_list_route__with_methods__and__with_url_path(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False, methods=['post'], url_path='action-one')
            def action1(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_route = self.get_dynamic_route_by_def_name('action1', routes)

        msg = '@list_route should map methods to "url_path"'
        self.assertEqual(action1_route.mapping, {'post': 'action1'}, msg)

        msg = '@list_route should use url in list scope with "url_path" value'
        self.assertEqual(action1_route.url, u'^{prefix}/action-one{trailing_slash}$', msg)

    def test_list_route_and_detail_route_with_exact_names(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False, url_path='action-one')
            def action1(self, request, *args, **kwargs):
                pass

            @action(detail=True, url_path='action-one')
            def action1_detail(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action1_detail_route = self.get_dynamic_route_by_def_name('action1_detail', routes)

        self.assertEqual(action1_list_route.mapping, {'get': 'action1'})
        self.assertEqual(action1_list_route.url, u'^{prefix}/action-one{trailing_slash}$')

        self.assertEqual(action1_detail_route.mapping, {'get': 'action1_detail'})
        self.assertEqual(action1_detail_route.url, u'^{prefix}/{lookup}/action-one{trailing_slash}$')

    def test_list_route_and_detail_route_names(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False)
            def action1(self, request, *args, **kwargs):
                pass

            @action(detail=True)
            def action2(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action2_detail_route = self.get_dynamic_route_by_def_name('action2', routes)

        self.assertEqual(action1_list_route.name, u'{basename}-action1')
        self.assertEqual(action2_detail_route.name, u'{basename}-action2')

    def test_list_route_and_detail_route_default_names__with_endpoints(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False, url_path='action_one')
            def action1(self, request, *args, **kwargs):
                pass

            @action(detail=True, url_path='action-two')
            def action2(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action2_detail_route = self.get_dynamic_route_by_def_name('action2', routes)

        self.assertEqual(action1_list_route.name, u'{basename}-action1')
        self.assertEqual(action2_detail_route.name, u'{basename}-action2')

    def test_list_route_and_detail_route_names__with_endpoints(self):
        class BasicViewSet(viewsets.ViewSet):
            @action(detail=False, url_path='action_one', url_name='action_one')
            def action1(self, request, *args, **kwargs):
                pass

            @action(detail=True, url_path='action-two', url_name='action-two')
            def action2(self, request, *args, **kwargs):
                pass

        routes = self.router.get_routes(BasicViewSet)
        action1_list_route = self.get_dynamic_route_by_def_name('action1', routes)
        action2_detail_route = self.get_dynamic_route_by_def_name('action2', routes)

        self.assertEqual(action1_list_route.name, u'{basename}-action_one')
        self.assertEqual(action2_detail_route.name, u'{basename}-action-two')
