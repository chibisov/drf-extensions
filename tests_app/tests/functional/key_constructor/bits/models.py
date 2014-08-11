# -*- coding: utf-8 -*-
from django.db import models


class KeyConstructorUserProperty(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests_app'


class KeyConstructorUserModel(models.Model):
    property = models.ForeignKey(KeyConstructorUserProperty)

    class Meta:
        app_label = 'tests_app'