# -*- coding: utf-8 -*-
from rest_framework import views
from rest_framework.response import Response

from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.key_constructor.bits import (
    QueryParamsKeyBit,
)
from rest_framework_extensions.key_constructor.constructors import (
    DefaultKeyConstructor,
)

# This parameter is used by the params constructor and the HelloParamView view.
# Both the constructor and the decorator must list which parameters are unique
# to this cache key.
TEST_PARAM = 'param'


class _ParamsConstructor(DefaultKeyConstructor):
    param_bit = QueryParamsKeyBit([TEST_PARAM])


class HelloView(views.APIView):
    """ normal test that uses the DefaultKeyConstructor
    """
    @cache_response()
    def get(self, request, *args, **kwargs):
        return Response('Hello world')


class HelloParamView(views.APIView):
    """ query parameter caching from the QueryParamsKeyBit key bit
    """
    @cache_response(key_func=_ParamsConstructor())
    def get(self, request, *args, **kwargs):
        param = request.GET.get(TEST_PARAM)
        return Response('Hello ' + param)
