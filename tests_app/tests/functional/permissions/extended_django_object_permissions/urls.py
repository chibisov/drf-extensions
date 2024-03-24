from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentViewSetPermissionFilterBackend,
    CommentViewSetWithoutHidingForbiddenObjects,
    CommentViewSetWithoutHidingForbiddenObjectsPermissionFilterBackend
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet, basename='alt1')
viewset_router.register('comments-permission-filter-backend', CommentViewSetPermissionFilterBackend, basename='alt2')
viewset_router.register('comments-without-hiding-forbidden-objects', CommentViewSetWithoutHidingForbiddenObjects, basename='alt3')
viewset_router.register(
    'comments-without-hiding-forbidden-objects-permission-filter-backend',
    CommentViewSetWithoutHidingForbiddenObjectsPermissionFilterBackend,
    basename='alt4'
)
urlpatterns = viewset_router.urls
