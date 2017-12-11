# -*- coding: utf-8 -*-
import django_filters
from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import ListETAGMixin, RetrieveETAGMixin

from .models import KeyConstructorUserModel as UserModel
from .serializers import UserModelSerializer


class UserModelViewSet(ListETAGMixin, RetrieveETAGMixin, viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('property',)
