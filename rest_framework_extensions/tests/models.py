# -*- coding: utf-8 -*-
from django.db import models


class DRFExtensionsModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """
    class Meta:
        app_label = 'tests'
        abstract = True


class Comment(DRFExtensionsModel):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)