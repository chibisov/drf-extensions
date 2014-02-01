# -*- coding: utf-8 -*-
from django.db import models


class Comment(models.Model):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'tests_app'