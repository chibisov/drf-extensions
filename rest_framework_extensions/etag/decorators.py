# -*- coding: utf-8 -*-
import logging
from functools import wraps

from django.utils.decorators import available_attrs
from django.utils.http import parse_etags, quote_etag

from rest_framework import status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from rest_framework_extensions.utils import prepare_header_name
from rest_framework_extensions.settings import extensions_api_settings
from django.utils import six


logger = logging.getLogger('django.request')


class ETAGProcessor(object):
    """Based on https://github.com/django/django/blob/master/django/views/decorators/http.py"""
    def __init__(self, etag_func=None, rebuild_after_method_evaluation=False):
        if not etag_func:
            etag_func = extensions_api_settings.DEFAULT_ETAG_FUNC
        self.etag_func = etag_func
        self.rebuild_after_method_evaluation = rebuild_after_method_evaluation

    def __call__(self, func):
        this = self
        @wraps(func, assigned=available_attrs(func))
        def inner(self, request, *args, **kwargs):
            return this.process_conditional_request(
                view_instance=self,
                view_method=func,
                request=request,
                args=args,
                kwargs=kwargs,
            )
        return inner

    def process_conditional_request(self,
                                    view_instance,
                                    view_method,
                                    request,
                                    args,
                                    kwargs):
        etags, if_none_match, if_match = self.get_etags_and_matchers(request)
        res_etag = self.calculate_etag(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs,
        )

        if self.is_if_none_match_failed(res_etag, etags, if_none_match):
            if request.method in SAFE_METHODS:
                response = Response(status=status.HTTP_304_NOT_MODIFIED)
            else:
                response = self._get_and_log_precondition_failed_response(request=request)
        elif self.is_if_match_failed(res_etag, etags, if_match):
            response = self._get_and_log_precondition_failed_response(request=request)
        else:
            response = view_method(view_instance, request, *args, **kwargs)
            if self.rebuild_after_method_evaluation:
                res_etag = self.calculate_etag(
                    view_instance=view_instance,
                    view_method=view_method,
                    request=request,
                    args=args,
                    kwargs=kwargs,
                )

        if res_etag and not response.has_header('ETag'):
            response['ETag'] = quote_etag(res_etag)

        return response

    def get_etags_and_matchers(self, request):
        etags = None
        if_none_match = request.META.get(prepare_header_name("if-none-match"))
        if_match = request.META.get(prepare_header_name("if-match"))
        if if_none_match or if_match:
            # There can be more than one ETag in the request, so we
            # consider the list of values.
            try:
                etags = parse_etags(if_none_match or if_match)
            except ValueError:
                # In case of invalid etag ignore all ETag headers.
                # Apparently Opera sends invalidly quoted headers at times
                # (we should be returning a 400 response, but that's a
                # little extreme) -- this is Django bug #10681.
                if_none_match = None
                if_match = None
        return etags, if_none_match, if_match

    def calculate_etag(self,
                       view_instance,
                       view_method,
                       request,
                       args,
                       kwargs):
        if isinstance(self.etag_func, six.string_types):
            etag_func = getattr(view_instance, self.etag_func)
        else:
            etag_func = self.etag_func
        return etag_func(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs,
        )

    def is_if_none_match_failed(self, res_etag, etags, if_none_match):
        if res_etag and if_none_match:
            return res_etag in etags or '*' in etags
        else:
            return False

    def is_if_match_failed(self, res_etag, etags, if_match):
        if res_etag and if_match:
            return res_etag not in etags and '*' not in etags
        else:
            return False

    def _get_and_log_precondition_failed_response(self, request):
        logger.warning('Precondition Failed: %s', request.path,
            extra={
                'status_code': status.HTTP_200_OK,
                'request': request
            }
        )
        return Response(status=status.HTTP_412_PRECONDITION_FAILED)


etag = ETAGProcessor