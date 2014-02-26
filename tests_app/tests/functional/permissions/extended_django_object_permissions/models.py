# -*- coding: utf-8 -*-
from django.db import models


class PermissionsComment(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        permissions = (
            ('view_permissionscomment', 'Can view comment'),
            # add, change, delete built in to django
        )
        app_label = 'tests_app'