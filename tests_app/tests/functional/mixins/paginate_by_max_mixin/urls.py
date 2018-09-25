from rest_framework import routers

from .views import (
    CommentViewSet,
    CommentWithoutPaginateByParamViewSet,
    CommentWithoutMaxPaginateByAttributeViewSet,
)


viewset_router = routers.DefaultRouter()
viewset_router.register('comments', CommentViewSet)
viewset_router.register('comments-without-paginate-by-param-attribute', CommentWithoutPaginateByParamViewSet)
viewset_router.register('comments-without-max-paginate-by-attribute', CommentWithoutMaxPaginateByAttributeViewSet)
urlpatterns = viewset_router.urls
