# -*- coding: utf-8 -*-
from django.db import models


class CommentForListDestroyModelMixin(models.Model):
    email = models.EmailField()

    class Meta:
        app_label = 'tests_app'