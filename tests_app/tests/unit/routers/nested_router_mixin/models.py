# -*- coding: utf-8 -*-
from django.db import models


class UnitNestedRouterMixinUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField('UnitNestedRouterMixinGroupModel', related_name='user_groups')

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'user'


class UnitNestedRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('UnitNestedRouterMixinPermissionModel')

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'group'


class UnitNestedRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'permission'