from rest_framework_extensions.mixins import PaginateByMaxMixin
from rest_framework.pagination import PageNumberPagination


class WithMaxPagination(PaginateByMaxMixin, PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 20


class FlexiblePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class FixedPagination(PageNumberPagination):
    page_size = 10
