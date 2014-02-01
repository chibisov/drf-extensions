# -*- coding: utf-8 -*-
from rest_framework import viewsets

from rest_framework_extensions.decorators import action
from .models import RouterTestModel


class RouterViewSet(viewsets.ModelViewSet):
    model = RouterTestModel

    @action()
    def detail_controller(self):
        pass

    @action(is_for_list=True)
    def list_controller(self):
        pass