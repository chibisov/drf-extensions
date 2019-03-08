import django_filters
from rest_framework import viewsets

from .models import KeyConstructorUserModel as UserModel
from .serializers import UserModelSerializer


class UserModelViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('property',)
