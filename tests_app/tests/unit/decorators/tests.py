from django.test import TestCase
from rest_framework import pagination, viewsets
from rest_framework_extensions.decorators import paginate


class TestPaginateDecorator(TestCase):

    def test_empty_pagination_class(self):
        msg = "@paginate missing required argument: 'pagination_class'"
        with self.assertRaisesMessage(AssertionError, msg):
            @paginate()
            class MockGenericViewSet(viewsets.GenericViewSet):
                pass

    def test_adding_page_number_pagination(self):
        """
        Other default pagination classes' test result will be same as this even if kwargs changed to anything.
        """

        @paginate(pagination_class=pagination.PageNumberPagination, page_size=5, ordering='-created_at')
        class MockGenericViewSet(viewsets.GenericViewSet):
            pass

        assert hasattr(MockGenericViewSet, 'pagination_class')
        assert MockGenericViewSet.pagination_class().page_size == 5
        assert MockGenericViewSet.pagination_class().ordering == '-created_at'

    def test_adding_custom_pagination(self):
        class CustomPagination(pagination.BasePagination):
            pass

        @paginate(pagination_class=CustomPagination, kwarg1='kwarg1', kwarg2='kwarg2')
        class MockGenericViewSet(viewsets.GenericViewSet):
            pass

        assert hasattr(MockGenericViewSet, 'pagination_class')
        assert MockGenericViewSet.pagination_class().kwarg1 == 'kwarg1'
        assert MockGenericViewSet.pagination_class().kwarg2 == 'kwarg2'
