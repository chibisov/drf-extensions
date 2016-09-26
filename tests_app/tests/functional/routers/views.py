# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route

from .models import RouterTestModel


class RouterViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()

    @detail_route()
    def detail_controller(self):
        pass

    @list_route()
    def list_controller(self):
        pass
