from django.db import models


class RelatedModel(models.Model):
    name = models.CharField(max_length=100)


class SomeModel(models.Model):
    name = models.CharField(max_length=100)
    related_model = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)
