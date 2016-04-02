# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework_extensions import serializers as drf_serializers
from django.contrib.auth.models import User
from .models import CommentModel


class UserSerializer(drf_serializers.PartialUpdateSerializerMixin,
                     serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'comments'
        )


class CommentSerializer(drf_serializers.PartialUpdateSerializerMixin,
                        serializers.ModelSerializer):
    title_from_source = serializers.CharField(source='title', required=False)

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'user',
            'users_liked',
            'title',
            'text',
            'attachment',
            'hidden_text'
        )


class CommentSerializerWithAllowedUserId(CommentSerializer):
    user_id = serializers.IntegerField()

    class Meta(CommentSerializer.Meta):
        fields = ('user_id',) + CommentSerializer.Meta.fields


class CommentSerializerWithExpandedUsersLiked(drf_serializers.PartialUpdateSerializerMixin,
                                              serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = CommentModel
        fields = (
            'title',
            'user'
        )
