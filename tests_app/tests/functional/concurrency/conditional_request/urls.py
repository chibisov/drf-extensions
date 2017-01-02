from django.conf.urls import url, include
from rest_framework import routers
from .views import BookViewSet, BookListCreateView, BookChangeView, BookCustomDestroyView

router = routers.DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    # manually add endpoints for APIView instances
    url(r'books_view/(?P<pk>[0-9]+)/custom_delete/', BookCustomDestroyView.as_view(), name='book_view-custom_delete'),
    url(r'books_view/', BookListCreateView.as_view(), name='book_view-list'),
    url(r'books_view/(?P<pk>[0-9]+)/', BookChangeView.as_view(), name='book_view-detail'),

    # include the URLs from the default viewset
    url(r'^', include(router.urls)),
]
