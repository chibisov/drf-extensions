# -*- coding: utf-8 -*-
from rest_framework import routers

from .views import CommentViewSet, CommentViewSetWithPermissions, UserViewSet


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet)
viewset_router.register('comments-with-permissions', CommentViewSetWithPermissions)
viewset_router.register('users', UserViewSet)
urlpatterns = viewset_router.urls
