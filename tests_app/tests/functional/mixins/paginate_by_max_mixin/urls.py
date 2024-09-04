from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentWithoutPaginateByParamViewSet,
    CommentWithoutMaxPaginateByAttributeViewSet,
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet, basename='1')
viewset_router.register('comments-without-paginate-by-param-attribute', CommentWithoutPaginateByParamViewSet, basename='2')
viewset_router.register('comments-without-max-paginate-by-attribute', CommentWithoutMaxPaginateByAttributeViewSet, basename='3')
urlpatterns = viewset_router.urls
