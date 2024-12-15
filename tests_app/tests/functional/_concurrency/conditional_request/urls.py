from django.urls import re_path, include
from rest_framework import routers
from .views import (BookViewSet, BookListCreateView, BookChangeView, BookCustomDestroyView,
                    BookUnconditionalDestroyView, BookUnconditionalUpdateView)

router = routers.DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    # manually add endpoints for APIView instances
    re_path(r'books_view/(?P<pk>[0-9]+)/custom/delete/', BookCustomDestroyView.as_view(), name='book_view-custom_delete'),
    re_path(r'books_view/(?P<pk>[0-9]+)/unconditional/delete/', BookUnconditionalDestroyView.as_view(),
        name='book_view-unconditional_delete'),
    re_path(r'books_view/(?P<pk>[0-9]+)/unconditional/update/', BookUnconditionalUpdateView.as_view(),
        name='book_view-unconditional_update'),
    re_path(r'books_view/', BookListCreateView.as_view(), name='book_view-list'),
    re_path(r'books_view/(?P<pk>[0-9]+)/', BookChangeView.as_view(), name='book_view-detail'),

    # include the URLs from the default viewset
    re_path(r'^', include(router.urls)),
]
