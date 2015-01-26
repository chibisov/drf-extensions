# -*- coding: utf-8 -*-
import warnings


def link(endpoint=None, is_for_list=False, **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for GET requests.
    """
    msg = 'link is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

    def decorator(func):
        func.bind_to_methods = ['get']
        func.kwargs = kwargs
        func.endpoint = endpoint or func.__name__
        func.is_for_list = is_for_list
        return func
    return decorator


def action(methods=['post'], endpoint=None, is_for_list=False, **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for POST requests.
    """
    msg = 'action is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

    def decorator(func):
        func.bind_to_methods = methods
        func.kwargs = kwargs
        func.endpoint = endpoint or func.__name__
        func.is_for_list = is_for_list
        return func
    return decorator

