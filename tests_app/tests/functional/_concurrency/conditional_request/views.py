from rest_framework import viewsets
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework_extensions.etag.mixins import APIETAGMixin
from rest_framework_extensions.etag.decorators import api_etag
from rest_framework_extensions.utils import default_api_object_etag_func
from .models import Book
from .serializers import BookSerializer


class BookViewSet(APIETAGMixin,
                  viewsets.ModelViewSet):
    """Test the mixin with DRF viewset."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookChangeView(APIETAGMixin,
                     generics.RetrieveUpdateDestroyAPIView):
    """Test the mixin with DRF generic API views."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookListCreateView(APIETAGMixin,
                         generics.ListCreateAPIView):
    """Test the mixin with DRF generic API views."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookCustomDestroyView(generics.DestroyAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@api_etag`
    queryset = Book.objects.all()

    @api_etag(etag_func=default_api_object_etag_func)
    def delete(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookUnconditionalDestroyView(generics.DestroyAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@api_etag`
    queryset = Book.objects.all()

    @api_etag(etag_func=default_api_object_etag_func, precondition_map={})
    def delete(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookUnconditionalUpdateView(generics.UpdateAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@api_etag`
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @api_etag(etag_func=default_api_object_etag_func, precondition_map={})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)