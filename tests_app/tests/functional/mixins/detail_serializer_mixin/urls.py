from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentWithoutDetailSerializerClassViewSet,
    CommentWithIdTwoViewSet,
    CommentWithIdTwoAndIdOneForDetailViewSet,
    CommentWithDetailSerializerAndNoArgsForGetQuerySetViewSet
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet, basename='alt1')
viewset_router.register('comments-2', CommentWithoutDetailSerializerClassViewSet, basename='alt2')
viewset_router.register('comments-3', CommentWithIdTwoViewSet, basename='alt3')
viewset_router.register('comments-4', CommentWithIdTwoAndIdOneForDetailViewSet, basename='alt4')
viewset_router.register('comments-5', CommentWithDetailSerializerAndNoArgsForGetQuerySetViewSet, basename='alt5')

urlpatterns = viewset_router.urls
