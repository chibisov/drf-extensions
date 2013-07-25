# -*- coding: utf-8 -*-


def link(endpoint=None, is_for_list=False, **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for GET requests.
    """
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
    def decorator(func):
        func.bind_to_methods = methods
        func.kwargs = kwargs
        func.endpoint = endpoint or func.__name__
        func.is_for_list = is_for_list
        return func
    return decorator