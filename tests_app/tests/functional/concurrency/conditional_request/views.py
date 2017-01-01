from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import APIETAGMixin
from .models import Book
from .serializers import BookSerializer


class BookViewSet(APIETAGMixin,
                  viewsets.ModelViewSet):

    queryset = Book.objects.all()
    serializer_class = BookSerializer
