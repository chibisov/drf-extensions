from django.db import models


class CommentForListUpdateModelMixin(models.Model):
    email = models.EmailField()


class UserForListUpdateModelMixin(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=10)
    age = models.IntegerField()
    last_name = models.CharField(max_length=10)
    password = models.CharField(max_length=100)
