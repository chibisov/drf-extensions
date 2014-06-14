# -*- coding: utf-8 -*-
from django.db import models


class CommentForListUpdateModelMixin(models.Model):
    email = models.EmailField()

    class Meta:
        app_label = 'tests_app'


class UserForListUpdateModelMixin(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=10)
    age = models.IntegerField()
    last_name = models.CharField(max_length=10)
    password = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests_app'