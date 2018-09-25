from django.db import models


class DefaultRouterUserModel(models.Model):
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField('DefaultRouterGroupModel', related_name='user_groups')


class DefaultRouterGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('DefaultRouterPermissionModel')


class DefaultRouterPermissionModel(models.Model):
    name = models.CharField(max_length=10)
