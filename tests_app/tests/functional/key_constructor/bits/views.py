# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import ListETAGMixin, RetrieveETAGMixin
from rest_framework.filters import DjangoFilterBackend

from .models import KeyConstructorUserModel as UserModel
from .serializers import UserModelSerializer


class UserModelViewSet(ListETAGMixin, RetrieveETAGMixin, viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('property',)