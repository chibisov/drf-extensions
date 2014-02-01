# -*- coding: utf-8 -*-
from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentWithoutDetailSerializerClassViewSet,
    CommentWithIdTwoViewSet,
    CommentWithIdTwoAndIdOneForDetailViewSet,
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet)
viewset_router.register('comments-2', CommentWithoutDetailSerializerClassViewSet)
viewset_router.register('comments-3', CommentWithIdTwoViewSet)
viewset_router.register('comments-4', CommentWithIdTwoAndIdOneForDetailViewSet)
urlpatterns = viewset_router.urls