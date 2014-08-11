# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework_extensions.etag.mixins import ListETAGMixin, RetrieveETAGMixin
from rest_framework.filters import DjangoFilterBackend

from .models import KeyConstructorUserModel as UserModel


class UserModelViewSet(ListETAGMixin, RetrieveETAGMixin, viewsets.ModelViewSet):
    model = UserModel
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('property',)