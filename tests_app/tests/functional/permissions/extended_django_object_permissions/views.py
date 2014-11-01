# -*- coding: utf-8 -*-
from rest_framework import viewsets, serializers
from rest_framework import authentication

try:
    from rest_framework.filters import DjangoObjectPermissionsFilter
except ImportError:
    class DjangoObjectPermissionsFilter(object):
        pass

try:
    from rest_framework_extensions.permissions import ExtendedDjangoObjectPermissions
except ImportError:
    class ExtendedDjangoObjectPermissions(object):
        pass

from .models import PermissionsComment


class CommentObjectPermissions(ExtendedDjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class PermissionsCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionsComment

class CommentObjectPermissionsWithoutHidingForbiddenObjects(CommentObjectPermissions):
    hide_forbidden_for_read_objects = False


class CommentViewSet(viewsets.ModelViewSet):
    queryset = PermissionsComment.objects.all()
    serializer_class = PermissionsCommentSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = (CommentObjectPermissions,)


class CommentViewSetPermissionFilterBackend(CommentViewSet):
    filter_backends = (DjangoObjectPermissionsFilter,)


class CommentViewSetWithoutHidingForbiddenObjects(CommentViewSet):
    permission_classes = (CommentObjectPermissionsWithoutHidingForbiddenObjects,)


class CommentViewSetWithoutHidingForbiddenObjectsPermissionFilterBackend(CommentViewSetWithoutHidingForbiddenObjects):
    filter_backends = (DjangoObjectPermissionsFilter,)