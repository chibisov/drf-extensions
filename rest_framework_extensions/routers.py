from copy import deepcopy
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_extensions.utils import compose_parent_pk_kwarg_name


class NestedRegistryItem:
    def __init__(self, router, parent_prefix, parent_item=None, parent_viewset=None, parent_lookups=[]):
        self.router = router
        self.parent_prefix = parent_prefix
        self.parent_item = parent_item
        self.parent_viewset = parent_viewset
        self.parent_lookups = parent_lookups

    def register(self, prefix, viewset, basename, parents_query_lookups=[], parent_query_lookup=""):
        # deepcopy to make sure one viewset class only has one parent viewset
        copied_viewset = deepcopy(viewset)
        if not parents_query_lookups:
            parents_query_lookups = ["__".join(
                [parent_query_lookup, pl]) for pl in self.parent_lookups] + [parent_query_lookup]

        self.router._register(
            prefix=self.get_prefix(
                current_prefix=prefix,
                parents_query_lookups=parents_query_lookups
            ),
            viewset=copied_viewset,
            basename=basename,
        )
        copied_viewset.parent_viewset = self.parent_viewset
        return NestedRegistryItem(
            router=self.router,
            parent_prefix=prefix,
            parent_item=self,
            parent_viewset=copied_viewset,
            parent_lookups=parents_query_lookups
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
        while current_item:
            parent_lookup_value_regex = getattr(
                current_item.parent_viewset, 'lookup_value_regex', '[^/.]+')
            prefix = '{parent_prefix}/(?P<{parent_pk_kwarg_name}>{parent_lookup_value_regex})/{prefix}'.format(
                parent_prefix=current_item.parent_prefix,
                parent_pk_kwarg_name=compose_parent_pk_kwarg_name(
                    parents_query_lookups[i]),
                parent_lookup_value_regex=parent_lookup_value_regex,
                prefix=prefix
            )
            i -= 1
            current_item = current_item.parent_item
        return prefix.strip('/')


class NestedRouterMixin:
    def _register(self, *args, **kwargs):
        return super().register(*args, **kwargs)

    def register(self, *args, **kwargs):
        self._register(*args, **kwargs)
        return NestedRegistryItem(
            router=self,
            parent_prefix=self.registry[-1][0],
            parent_viewset=self.registry[-1][1]
        )


class ExtendedRouterMixin(NestedRouterMixin):
    pass


class ExtendedSimpleRouter(ExtendedRouterMixin, SimpleRouter):
    pass


class ExtendedDefaultRouter(ExtendedRouterMixin, DefaultRouter):
    pass
