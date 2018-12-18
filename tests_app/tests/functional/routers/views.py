from rest_framework import viewsets
from rest_framework.decorators import action

from .models import RouterTestModel


class RouterViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()

    @action(detail=True)
    def detail_controller(self):
        pass

    @action(detail=False)
    def list_controller(self):
        pass
