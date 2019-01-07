import django
from django.db import models


class PermissionsComment(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        if django.VERSION < (2, 1):
            permissions = (
                ('view_permissionscomment', 'Can view comment'),
                # add, change, delete built in to django
            )
