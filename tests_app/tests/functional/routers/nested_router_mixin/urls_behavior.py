from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    UserViewSetWithEmailLookup,
    GroupViewSet,
)

router = ExtendedSimpleRouter()

# main routesconfiguration
(
    router.register(r'users', UserViewSetWithEmailLookup)
            .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user_groups__email'])
)

urlpatterns = [
    url(r'^', include(router.urls)),
]
