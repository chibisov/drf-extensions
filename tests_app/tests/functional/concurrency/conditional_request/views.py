from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import ETAGMixin
from rest_framework_extensions.key_constructor.constructors import ModelInstanceKeyConstructor
from .models import Book
from .serializers import BookSerializer


class BookViewSet(ETAGMixin,
                  viewsets.ModelViewSet):

    queryset = Book.objects.all()
    serializer_class = BookSerializer

    # use a custom object_etag_func (semantic hash of the object's contents)
    object_etag_func = ModelInstanceKeyConstructor()
