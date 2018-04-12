from django.db import models


class Book(models.Model):
    """A sample model for conditional requests."""

    name = models.CharField(max_length=100, default=None, blank=True, null=True)
    author = models.CharField(max_length=100, default=None, blank=True, null=True)
    issn = models.CharField(max_length=100, default=None, blank=True, null=True)
