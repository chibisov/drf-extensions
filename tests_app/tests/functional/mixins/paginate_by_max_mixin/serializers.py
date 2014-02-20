# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import CommentForPaginateByMaxMixin


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentForPaginateByMaxMixin
        fields = (
            'id',
            'email',
        )
