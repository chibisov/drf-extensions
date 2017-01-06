from rest_framework import viewsets
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework_extensions.decorators import precondition_required
from rest_framework_extensions.concurrency.mixins import OCCAPIETAGMixin
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.utils import default_api_object_etag_func
from .models import Book
from .serializers import BookSerializer


class BookViewSet(OCCAPIETAGMixin,
                  viewsets.ModelViewSet):
    """Test the mixin with DRF viewset."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookChangeView(OCCAPIETAGMixin,
                     generics.RetrieveUpdateDestroyAPIView):
    """Test the mixin with DRF generic API views."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookListCreateView(OCCAPIETAGMixin,
                         generics.ListCreateAPIView):
    """Test the mixin with DRF generic API views."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookCustomDestroyView(generics.DestroyAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@etag`
    queryset = Book.objects.all()

    # checks for an 'If-Match' header in the DELETE request (default behavior)
    @precondition_required()
    @etag(etag_func=default_api_object_etag_func)
    def delete(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookUnconditionalDestroyView(generics.DestroyAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@etag`
    queryset = Book.objects.all()

    @etag(etag_func=default_api_object_etag_func)
    def delete(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookUnconditionalUpdateView(generics.UpdateAPIView):
    """Test the decorator with DRF generic API views."""

    # include the queryset here to enable the object lookup in `@etag`
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @etag(etag_func=default_api_object_etag_func)
    def update(self, request, *args, **kwargs):
        return super(BookUnconditionalUpdateView, self).update(request, *args, **kwargs)
