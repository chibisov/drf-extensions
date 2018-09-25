from django.db import models


class UserModel(models.Model):
    name = models.CharField(max_length=20)


class CommentModel(models.Model):
    user = models.ForeignKey(
        UserModel,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    users_liked = models.ManyToManyField(UserModel, blank=True)
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=200)
    attachment = models.FileField(
        upload_to='test_serializers', blank=True, null=True, max_length=500)
    hidden_text = models.CharField(max_length=200, blank=True, null=True)
