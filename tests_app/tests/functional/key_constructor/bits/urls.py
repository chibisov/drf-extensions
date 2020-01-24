from rest_framework import routers

from .views import UserModelViewSet


viewset_router = routers.DefaultRouter()
viewset_router.register('users', UserModelViewSet)
urlpatterns = viewset_router.urls
