from django.db import models


class CommentForListDestroyModelMixin(models.Model):
    email = models.EmailField()
