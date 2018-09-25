from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentViewSetPermissionFilterBackend,
    CommentViewSetWithoutHidingForbiddenObjects,
    CommentViewSetWithoutHidingForbiddenObjectsPermissionFilterBackend
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet)
viewset_router.register('comments-permission-filter-backend', CommentViewSetPermissionFilterBackend)
viewset_router.register('comments-without-hiding-forbidden-objects', CommentViewSetWithoutHidingForbiddenObjects)
viewset_router.register(
    'comments-without-hiding-forbidden-objects-permission-filter-backend',
    CommentViewSetWithoutHidingForbiddenObjectsPermissionFilterBackend
)
urlpatterns = viewset_router.urls
