from django.db import models


class BitTestModel(models.Model):
    is_active = models.BooleanField(default=False)
