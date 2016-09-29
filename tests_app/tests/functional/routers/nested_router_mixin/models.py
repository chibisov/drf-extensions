# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class NestedRouterMixinUserModel(models.Model):
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField(
        'NestedRouterMixinGroupModel', related_name='user_groups')

    class Meta:
        app_label = 'tests_app'


class NestedRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('NestedRouterMixinPermissionModel')

    class Meta:
        app_label = 'tests_app'


class NestedRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = 'tests_app'


class NestedRouterMixinTaskModel(models.Model):
    title = models.CharField(max_length=30)

    class Meta:
        app_label = 'tests_app'


class NestedRouterMixinBookModel(models.Model):
    title = models.CharField(max_length=30)

    class Meta:
        app_label = 'tests_app'


class NestedRouterMixinCommentModel(models.Model):
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()
    text = models.CharField(max_length=30)

    class Meta:
        app_label = 'tests_app'