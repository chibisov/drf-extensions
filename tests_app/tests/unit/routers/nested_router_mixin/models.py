# -*- coding: utf-8 -*-
from django.db import models


class NestedRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'permission_app'
        verbose_name = 'permission'


class NestedRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField(
        'NestedRouterMixinPermissionModel')

    class Meta:
        app_label = 'group_app'
        verbose_name = 'group'


class NestedRouterMixinUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField(
        'NestedRouterMixinGroupModel', related_name='user_groups')

    class Meta:
        app_label = 'user_app'
        verbose_name = 'user'
