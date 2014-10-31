# -*- coding: utf-8 -*-
from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.cache.decorators import cache_response


class HelloView(views.APIView):
    @cache_response()
    def get(self, request, *args, **kwargs):
        return Response('Hello world')


class HelloParamView(views.APIView):
    @cache_response()
    def get(self, request, *args, **kwargs):
        param = request.GET.get("param")
        return Response('Hello ' + param)
