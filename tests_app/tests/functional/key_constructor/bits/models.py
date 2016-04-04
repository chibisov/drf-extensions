# -*- coding: utf-8 -*-
from django.db import models


class KeyConstructorUserProperty(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'keycon_user_prop'


class KeyConstructorUserModel(models.Model):
    property = models.ForeignKey(KeyConstructorUserProperty)

    class Meta:
        app_label = 'keycon_user'