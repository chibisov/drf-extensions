from rest_framework import routers

from .views import CommentViewSet, CommentViewSetWithPermissions, UserViewSet


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet, basename='alt1')
viewset_router.register('comments-with-permissions', CommentViewSetWithPermissions, basename='alt2')
viewset_router.register('users', UserViewSet, basename='alt3')
urlpatterns = viewset_router.urls
