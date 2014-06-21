# -*- coding: utf-8 -*-
from django.db import models


class NesterRouterMixinUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField('NesterRouterMixinGroupModel', related_name='user_groups')

    class Meta:
        app_label = 'tests_app'


class NesterRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('NesterRouterMixinPermissionModel')

    class Meta:
        app_label = 'tests_app'


class NesterRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'tests_app'