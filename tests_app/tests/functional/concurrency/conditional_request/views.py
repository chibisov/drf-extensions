from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import ETAGMixin
from .models import Book
from .serializers import BookSerializer


class BookViewSet(ETAGMixin,
                  viewsets.ModelViewSet):

    queryset = Book.objects.all()
    serializer_class = BookSerializer
