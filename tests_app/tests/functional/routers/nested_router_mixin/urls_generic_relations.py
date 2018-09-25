from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    TaskViewSet,
    TaskCommentViewSet,
    BookViewSet,
    BookCommentViewSet
)


router = ExtendedSimpleRouter()
# tasks route
(
    router.register(r'tasks', TaskViewSet)
          .register(r'comments', TaskCommentViewSet, 'tasks-comment', parents_query_lookups=['object_id'])
)
# books route
(
    router.register(r'books', BookViewSet)
          .register(r'comments', BookCommentViewSet, 'books-comment', parents_query_lookups=['object_id'])
)

urlpatterns = router.urls
