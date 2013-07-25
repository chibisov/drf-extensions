# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured

from rest_framework.routers import (
    DefaultRouter,
    SimpleRouter,
    Route,
    replace_methodname,
    flatten
)


class ExtendedActionLinkRouterMixin(object):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}/$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}/$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated routes.
        # Generated using @action or @link decorators on methods of the viewset.
        # List
        Route(
            url=r'^{prefix}/{methodname}/$',
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}-list',
            initkwargs={}
        ),
        # Detail
        Route(
            url=r'^{prefix}/{lookup}/{methodname}/$',
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
    ]
    _routs = routes[2:4] + routes[:2]  # first routes should be dynamic (because of urlpatterns position matters)
                                       # left self.routs for backward

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """

        # Determine any `@action` or `@link` decorated methods on the viewset
        dynamic_routes = self.get_dynamic_routes(viewset)

        ret = []
        for route in self._routs:
            if self.is_dynamic_route(route):
                # Dynamic routes (@link or @action decorator)
                if self.is_list_dynamic_route(route):
                    ret += self.get_dynamic_routes_instances(
                        viewset,
                        route,
                        self._filter_by_list_dynamic_routes(dynamic_routes)
                    )
                else:
                    ret += self.get_dynamic_routes_instances(
                        viewset,
                        route,
                        self._filter_by_detail_dynamic_routes(dynamic_routes)
                    )
            else:
                # Standard route
                ret.append(route)

        return ret

    def _filter_by_list_dynamic_routes(self, dynamic_routes):
        return [i for i in dynamic_routes if i[3]]

    def _filter_by_detail_dynamic_routes(self, dynamic_routes):
        return [i for i in dynamic_routes if not i[3]]

    def get_dynamic_routes(self, viewset):
        known_actions = self.get_known_actions()
        dynamic_routes = []
        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethods = getattr(attr, 'bind_to_methods', None)
            if httpmethods:
                endpoint = getattr(attr, 'endpoint')
                is_for_list = getattr(attr, 'is_for_list')
                if endpoint in known_actions:
                    raise ImproperlyConfigured('Cannot use @action or @link decorator on '
                                               'method "%s" as %s is an existing route'
                                               % (methodname, endpoint))
                httpmethods = [method.lower() for method in httpmethods]
                dynamic_routes.append((httpmethods, methodname, endpoint, is_for_list))
        return dynamic_routes

    def get_dynamic_route_viewset_method_name_by_endpoint(self, viewset, endpoint):
        for dynamic_route in self.get_dynamic_routes(viewset=viewset):
            if dynamic_route[2] == endpoint:
                return dynamic_route[1]

    def get_known_actions(self):
        return flatten([route.mapping.values() for route in self.routes])

    def is_dynamic_route(self, route):
        return route.mapping == {'{httpmethod}': '{methodname}'}

    def is_list_dynamic_route(self, route):
        return route.name == '{basename}-{methodnamehyphen}-list'

    def get_dynamic_routes_instances(self, viewset, route, dynamic_routes):
        dynamic_routes_instances = []
        for httpmethods, methodname, endpoint, is_for_list in dynamic_routes:
            initkwargs = route.initkwargs.copy()
            initkwargs.update(getattr(viewset, methodname).kwargs)
            dynamic_routes_instances.append(Route(
                url=replace_methodname(route.url, endpoint),
                mapping=dict((httpmethod, methodname) for httpmethod in httpmethods),
                name=replace_methodname(route.name, endpoint),
                initkwargs=initkwargs,
            ))
        return dynamic_routes_instances


class ExtendedSimpleRouter(ExtendedActionLinkRouterMixin, SimpleRouter):
    pass


class ExtendedDefaultRouter(ExtendedActionLinkRouterMixin, DefaultRouter):
    pass