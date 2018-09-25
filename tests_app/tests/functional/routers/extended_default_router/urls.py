from rest_framework_extensions.routers import ExtendedDefaultRouter

from .views import (
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)


router = ExtendedDefaultRouter()
# nested routes
(
    router.register(r'users', UserViewSet)
          .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user_groups'])
          .register(r'permissions', PermissionViewSet, 'users-groups-permission', parents_query_lookups=['group__user', 'group'])
)
# simple routes
router.register(r'groups', GroupViewSet, 'group')
router.register(r'permissions', PermissionViewSet, 'permission')

urlpatterns = router.urls
