# -*- coding: utf-8 -*-
from django.db import models


class BitTestModel(models.Model):
    is_active = models.BooleanField()

    class Meta:
        app_label = 'tests_app'