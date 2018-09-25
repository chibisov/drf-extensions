from rest_framework import viewsets

from .pagination import WithMaxPagination, FixedPagination, FlexiblePagination
from .models import CommentForPaginateByMaxMixin
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = WithMaxPagination
    queryset = CommentForPaginateByMaxMixin.objects.all().order_by('id')


class CommentWithoutPaginateByParamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = FixedPagination
    queryset = CommentForPaginateByMaxMixin.objects.all()


class CommentWithoutMaxPaginateByAttributeViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = FlexiblePagination
    serializer_class = CommentSerializer
    queryset = CommentForPaginateByMaxMixin.objects.all()
