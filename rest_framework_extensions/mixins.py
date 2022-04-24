from rest_framework_extensions.cache.mixins import CacheResponseMixin
from django.core.exceptions import ValidationError
# from rest_framework_extensions.etag.mixins import ReadOnlyETAGMixin, ETAGMixin
from django.http import Http404
from rest_framework_extensions.bulk_operations.mixins import ListUpdateModelMixin, ListDestroyModelMixin
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework import status, exceptions
from rest_framework.generics import get_object_or_404


class DetailSerializerMixin:
    """
    Add custom serializer for detail view
    """
    serializer_detail_class = None
    queryset_detail = None

    def get_serializer_class(self):
        error_message = "'{0}' should include a 'serializer_detail_class' attribute".format(
            self.__class__.__name__)
        assert self.serializer_detail_class is not None, error_message
        if self._is_request_to_detail_endpoint():
            return self.serializer_detail_class
        else:
            return super().get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        if self._is_request_to_detail_endpoint() and self.queryset_detail is not None:
            return self.queryset_detail.all()  # todo: test all()
        else:
            return super().get_queryset(*args, **kwargs)

    def _is_request_to_detail_endpoint(self):
        if hasattr(self, 'lookup_url_kwarg'):
            lookup = self.lookup_url_kwarg or self.lookup_field
        return lookup and lookup in self.kwargs


class PaginateByMaxMixin:

    def get_page_size(self, request):
        if self.page_size_query_param and self.max_page_size and request.query_params.get(self.page_size_query_param) == 'max':
            return self.max_page_size
        return super().get_page_size(request)


# class ReadOnlyCacheResponseAndETAGMixin(ReadOnlyETAGMixin, CacheResponseMixin):
#     pass


# class CacheResponseAndETAGMixin(ETAGMixin, CacheResponseMixin):
#     pass


class NestedViewSetMixin:
    parent_viewsets = set()

    def check_ownership(self, serializer):
        parent_query_dicts = self.get_parents_query_dict()
        if parent_query_dicts:
            parent_name, parent_value = list(parent_query_dicts.items())[-1]
            items = serializer.validated_data
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if item.get(parent_name, None) is None:
                    raise exceptions.PermissionDenied(
                        detail=f"You must specific '{parent_name}'", code=status.HTTP_403_FORBIDDEN)
                if item.get(parent_name, None) != parent_value:
                    raise exceptions.PermissionDenied(
                        detail=f"You don't have permission to operate item that belone to '{parent_name}:{parent_value}'", code=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        self.check_ownership(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self.check_ownership(serializer)
        super().perform_update(serializer)

    def check_parent_object_permissions(self, request):
        # if parent viewset haven't init yet, then will raise no "kwargs" attribute error, but it doesn't matter, just ignore
        try:
            parents_query_dict = self.get_parents_query_dict()
        except:
            return
        if not parents_query_dict:
            return
        current_model = self.get_queryset().model
        # TODO
        # 1. for model__submodel case(Done).
        # 2. for generic relations case.
        for parent_model_lookup_name, parent_model_lookup_value in reversed(parents_query_dict.items()):
            parent_model = current_model
            for lookup_name in parent_model_lookup_name.split("__"):
                parent_model = parent_model._meta.get_field(
                    lookup_name).related_model
            for parent_viewset_class in self.parent_viewsets:
                parent_viewset = parent_viewset_class()
                parent_viewset_model = getattr(
                    parent_viewset, "model", None) or parent_viewset.queryset.model
                if parent_viewset_model == parent_model:
                    parent_obj = get_object_or_404(
                        parent_viewset_model.objects.all(),
                        **{parent_viewset.lookup_field: parent_model_lookup_value}
                    )
                    parent_viewset.check_object_permissions(
                        request, parent_obj
                    )
            current_model = parent_model

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.parent_viewsets:
            self.check_parent_object_permissions(request)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.parent_viewsets:
            self.check_parent_object_permissions(request)

    def get_queryset(self):
        return self.filter_queryset_by_parents_lookups(
            super().get_queryset()
        )

    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        if parents_query_dict:
            try:
                return queryset.filter(**parents_query_dict)
            except ValueError:
                raise Http404
        else:
            return queryset

    def get_parents_query_dict(self):
        result = {}
        for kwarg_name, kwarg_value in self.kwargs.items():
            if kwarg_name.startswith(extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX):
                query_lookup = kwarg_name.replace(
                    extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX,
                    '',
                    1
                )
                query_value = kwarg_value
                result[query_lookup] = query_value
        return result
