# -*- coding: utf-8 -*-
from django.db import models


class UnitNesterRouterMixinUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField('NesterRouterMixinGroupModel')

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'user'


class UnitNesterRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('NesterRouterMixinPermissionModel')

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'group'


class UnitNesterRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'permission'