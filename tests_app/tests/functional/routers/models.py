from django.db import models


class RouterTestModel(models.Model):
    uuid = models.CharField(max_length=20)
    text = models.CharField(max_length=200)