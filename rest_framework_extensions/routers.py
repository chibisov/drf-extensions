# -*- coding: utf-8 -*-
from distutils.version import StrictVersion
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch

import rest_framework
from rest_framework.routers import (
    DefaultRouter,
    SimpleRouter,
    Route,
    replace_methodname,
)
from rest_framework import views
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework_extensions.utils import flatten, compose_parent_pk_kwarg_name
from rest_framework_extensions.compat_drf import add_trailing_slash_if_needed


class ExtendedActionLinkRouterMixin(object):
    routes = [
        # List route.
        Route(
            url=add_trailing_slash_if_needed(r'^{prefix}/$'),
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=add_trailing_slash_if_needed(r'^{prefix}/{lookup}/$'),
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
        # Generated using @list_route or @detail_route decorators on methods of the viewset.
        # List
        Route(
            url=add_trailing_slash_if_needed(r'^{prefix}/{methodname}/$'),
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}-list',
            initkwargs={}
        ),
        # Detail
        Route(
            url=add_trailing_slash_if_needed(r'^{prefix}/{lookup}/{methodname}/$'),
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

        # Determine any `@list_route` or `@detail_route` decorated methods on the viewset
        dynamic_routes = self.get_dynamic_routes(viewset)

        ret = []
        for route in self._routs:
            if self.is_dynamic_route(route):
                # Dynamic routes (@list_route or @detail_route decorator)
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
                endpoint = getattr(attr, 'endpoint', methodname)
                is_for_list = getattr(attr, 'is_for_list', not getattr(attr, 'detail', True))
                if endpoint in known_actions:
                    raise ImproperlyConfigured('Cannot use @detail_route or @list_route decorator on '
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
            url_path = initkwargs.pop('url_path', endpoint)
            dynamic_routes_instances.append(Route(
                url=replace_methodname(route.url, url_path),
                mapping=dict((httpmethod, methodname) for httpmethod in httpmethods),
                name=replace_methodname(route.name, url_path),
                initkwargs=initkwargs,
            ))
        return dynamic_routes_instances


class NestedRegistryItem(object):
    def __init__(self, router, parent_prefix, parent_item=None, parent_viewset=None):
        self.router = router
        self.parent_prefix = parent_prefix
        self.parent_item = parent_item
        self.parent_viewset = parent_viewset

    def register(self, prefix, viewset, base_name, parents_query_lookups):
        self.router._register(
            prefix=self.get_prefix(current_prefix=prefix, parents_query_lookups=parents_query_lookups),
            viewset=viewset,
            base_name=base_name,
        )
        return NestedRegistryItem(
            router=self.router,
            parent_prefix=prefix,
            parent_item=self,
            parent_viewset=viewset
        )

    def get_prefix(self, current_prefix, parents_query_lookups):
        return '{0}/{1}'.format(
            self.get_parent_prefix(parents_query_lookups),
            current_prefix
        )

    def get_parent_prefix(self, parents_query_lookups):
        prefix = '/'
        current_item = self
        i = len(parents_query_lookups) - 1
        parent_lookup_value_regex = getattr(self.parent_viewset, 'lookup_value_regex', '[^/.]+')
        while current_item:
            prefix = '{parent_prefix}/(?P<{parent_pk_kwarg_name}>{parent_lookup_value_regex})/{prefix}'.format(
                parent_prefix=current_item.parent_prefix,
                parent_pk_kwarg_name=compose_parent_pk_kwarg_name(parents_query_lookups[i]),
                parent_lookup_value_regex=parent_lookup_value_regex,
                prefix=prefix
            )
            i -= 1
            current_item = current_item.parent_item
        return prefix.strip('/')


class NestedRouterMixin(object):
    def _register(self, *args, **kwargs):
        return super(NestedRouterMixin, self).register(*args, **kwargs)

    def register(self, *args, **kwargs):
        self._register(*args, **kwargs)
        return NestedRegistryItem(
            router=self,
            parent_prefix=self.registry[-1][0],
            parent_viewset=self.registry[-1][1]
        )

    def get_api_root_view(self, **kwargs):
        """
        Return a view to use as the API root.
        Important to maintain compat with DRF 3.4.0
        """
        if StrictVersion(rest_framework.VERSION) >= StrictVersion('3.4.0'):
            return super(NestedRouterMixin, self).get_api_root_view(**kwargs)
        if StrictVersion(rest_framework.VERSION) >= StrictVersion('2.4.3'):
            return super(NestedRouterMixin, self).get_api_root_view()
        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get(self, request, format=None):
                ret = {}
                for key, url_name in api_root_dict.items():
                    try:
                        ret[key] = reverse(url_name, request=request, format=format)
                    except NoReverseMatch:
                        pass
                return Response(ret)

        return APIRoot.as_view()


class ExtendedRouterMixin(ExtendedActionLinkRouterMixin, NestedRouterMixin):
    pass


class ExtendedSimpleRouter(ExtendedRouterMixin, SimpleRouter):
    pass


class ExtendedDefaultRouter(ExtendedRouterMixin, DefaultRouter):
    pass
