# -*- coding: utf-8 -*-
from rest_framework import viewsets

from .models import RouterTestModel


class RouterViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()
