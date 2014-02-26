# -*- coding: utf-8 -*-
from rest_framework_extensions.utils import get_rest_framework_features


if get_rest_framework_features()['django_object_permissions_class']:
    from .extended_django_object_permissions import ExtendedDjangoObjectPermissions