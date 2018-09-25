from django.db import models


class NestedRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)


class NestedRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField(
        'NestedRouterMixinPermissionModel')


class NestedRouterMixinUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField(
        'NestedRouterMixinGroupModel', related_name='user_groups')
