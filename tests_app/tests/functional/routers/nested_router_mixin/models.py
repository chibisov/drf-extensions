from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey


class NestedRouterMixinUserModel(models.Model):
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=10)
    groups = models.ManyToManyField(
        'NestedRouterMixinGroupModel', related_name='user_groups')


class NestedRouterMixinGroupModel(models.Model):
    name = models.CharField(max_length=10)
    permissions = models.ManyToManyField('NestedRouterMixinPermissionModel')


class NestedRouterMixinPermissionModel(models.Model):
    name = models.CharField(max_length=10)


class NestedRouterMixinTaskModel(models.Model):
    title = models.CharField(max_length=30)


class NestedRouterMixinBookModel(models.Model):
    title = models.CharField(max_length=30)


class NestedRouterMixinCommentModel(models.Model):
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()
    text = models.CharField(max_length=30)
