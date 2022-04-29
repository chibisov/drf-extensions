from django.http import Http404
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework import status, exceptions
from rest_framework.generics import get_object_or_404

class BulkCreateModelMixin:
    """
    Builk create model instance.
    Just post data like:
    [
        {"name": "xxx"},
        {"name": "xxx2"},
    ]
    """

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        s = super().get_serializer(*args, **kwargs)
        return s


class MultiSerializerViewSetMixin:
    """
    serializer_action_classes = {
        list: ListSerializer,
        <action_name>: Serializer,
        ...
    }
    """
    serializer_classes = {}
    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MultiSerializerViewSetMixin, self).get_serializer_class()


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
    parent_viewset = None

    def check_ownership(self, serializer):
        parent_query_dicts = self.get_parents_query_dict()
        if not parent_query_dicts:
            return

        parent_lookup, parent_value = list(parent_query_dicts.items())[-1]
        if "__" in parent_lookup:
            receive_key, _ = parent_lookup.split("__")
        else:
            receive_key = parent_lookup

        instance_datas = serializer.validated_data
        if not isinstance(instance_datas, list):
            instance_datas = [instance_datas]
        received_parent_values = [
            i.get(receive_key) for i in instance_datas if i.get(receive_key)]

        # 1. check filled parent field
        if len(received_parent_values) != len(instance_datas):
            raise exceptions.PermissionDenied(
                detail=f"You must specific '{parent_lookup}'", code=status.HTTP_403_FORBIDDEN)

        received_parent_values = [str(v) if isinstance(v, (str, int)) else
                                  str(getattr(v, self.parent_viewset.lookup_field))
                                  for v in received_parent_values
                                  ]
        # 2. check direct FK parent
        if not "__" in parent_lookup:
            not_blong = [
                v for v in received_parent_values if v != str(parent_value)
            ]
            if not_blong:
                raise exceptions.PermissionDenied(
                    detail=f"You don't have permission to operate item that belong to '{parent_lookup}:{not_blong}'", code=status.HTTP_403_FORBIDDEN)
        else:
            # 3. for multiple layer parent
            direct_parent, direct_parent_look_field = parent_lookup.split(
                '__', 1)
            current_model = self.get_queryset().model
            direct_parent_model = current_model._meta.get_field(
                direct_parent
            ).related_model
            direct_parent_instances = direct_parent_model.objects.filter(
                **{f"pk__in": received_parent_values}
            )
            fields = direct_parent_look_field.split("__")
            for instance in direct_parent_instances:
                final_parent_obj = instance
                for f in fields:
                    final_parent_obj = getattr(instance, f)
                if (received_value := str(getattr(final_parent_obj, self.parent_viewset.lookup_field))) != str(parent_value):
                    raise exceptions.PermissionDenied(
                        detail=f"You don't have permission to operate item that belong to '{parent_lookup}:{received_value}'", code=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        self.check_ownership(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self.check_ownership(serializer)
        super().perform_update(serializer)

    def get_parent_model(self, current_model, parent_model_lookup_name):
        parent_model = current_model
        for lookup_name in parent_model_lookup_name.split("__"):
            parent_model = parent_model._meta.get_field(
                lookup_name).related_model
        return parent_model

    def check_parent_object_permissions(self, request):
        # if parent viewset haven't init yet, then will raise no "kwargs" attribute error, but it doesn't matter, just ignore
        try:
            if not (parents_query_dict := self.get_parents_query_dict()):
                return
        except:
            return
        # 2. for generic relations case.
        current_model = self.get_queryset().model
        current_viewset = self

        for parent_model_lookup_name, parent_model_lookup_value in sorted(parents_query_dict.items(), key=lambda item: len(item[0])):
            parent_model = self.get_parent_model(
                current_model, parent_model_lookup_name)
            parent_viewset = current_viewset.parent_viewset()

            parent_obj = get_object_or_404(
                parent_model.objects.all(),
                **{parent_viewset.lookup_field: parent_model_lookup_value}
            )
            parent_viewset.check_object_permissions(
                request, parent_obj
            )

            current_viewset = parent_viewset

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.parent_viewset:
            self.check_parent_object_permissions(request)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.parent_viewset:
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
