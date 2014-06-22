# -*- coding: utf-8 -*-
from django.db import models


class DefaultRouterUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField('DefaultRouterGroupModel', related_name='user_groups')

    class Meta:
        app_label = 'tests_app'


class DefaultRouterGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('DefaultRouterPermissionModel')

    class Meta:
        app_label = 'tests_app'


class DefaultRouterPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'tests_app'