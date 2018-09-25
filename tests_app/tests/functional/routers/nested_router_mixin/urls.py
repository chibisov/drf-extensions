from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)


router = ExtendedSimpleRouter()
# main routes
(
    router.register(r'users', UserViewSet)
          .register(r'groups', GroupViewSet, 'users-group', parents_query_lookups=['user_groups'])
          .register(r'permissions', PermissionViewSet, 'users-groups-permission', parents_query_lookups=['group__user', 'group'])
)

# register on one depth
permissions_routes = router.register(r'permissions', PermissionViewSet)
permissions_routes.register(r'groups', GroupViewSet, 'permissions-group', parents_query_lookups=['permissions'])
permissions_routes.register(r'users', UserViewSet, 'permissions-user', parents_query_lookups=['groups__permissions'])

# simple routes
router.register(r'groups', GroupViewSet, 'group')
router.register(r'permissions', PermissionViewSet, 'permission')

urlpatterns = router.urls
