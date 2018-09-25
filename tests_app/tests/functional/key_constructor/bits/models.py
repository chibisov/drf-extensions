from django.db import models


class KeyConstructorUserProperty(models.Model):
    name = models.CharField(max_length=100)


class KeyConstructorUserModel(models.Model):
    property = models.ForeignKey(
        KeyConstructorUserProperty,
        on_delete=models.CASCADE
    )
