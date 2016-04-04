# -*- coding: utf-8 -*-
import os

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class UserModel(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = 'tests_app'


upload_to = os.path.join(settings.FILE_STORAGE_DIR, 'test_serializers')


class CommentModel(models.Model):
    user = models.ForeignKey(User, related_name='comments')
    users_liked = models.ManyToManyField(User, blank=True, null=True)
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=200)
    attachment = models.FileField(
        upload_to=upload_to, blank=True, null=True, max_length=500)
    hidden_text = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.user

    class Meta:
        app_label = 'tests_app'
