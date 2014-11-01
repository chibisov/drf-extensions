# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import (
    UserForListUpdateModelMixin as User,
    CommentForListUpdateModelMixin as Comment,
)


class UserSerializer(serializers.ModelSerializer):
    surname = serializers.CharField(source='last_name')

    class Meta:
        model = User
        write_only_fields = ('password',)
        read_only_fields = ('name',)
        fields = [
            'id',
            'age',
            'name',
            'surname',
            'password'
        ]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment