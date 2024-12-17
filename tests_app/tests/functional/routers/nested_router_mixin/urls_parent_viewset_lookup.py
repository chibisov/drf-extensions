from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    UserViewSetWithEmailLookup,
    UserViewSetWithUUIDLookup,
    GroupViewSet,
)


router = ExtendedSimpleRouter()

# main routes
(
    router.register(r'users', UserViewSetWithEmailLookup, basename='users-by-uuid')
          .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user_groups__email'])
)

# uuid routes
(
    router.register(r'users-by-uuid', UserViewSetWithUUIDLookup)
          .register(r'groups', GroupViewSet, 'users-group-uuid', parents_query_lookups=['user_groups__code'])
)

urlpatterns = router.urls
