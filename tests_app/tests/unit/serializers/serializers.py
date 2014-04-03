# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework_extensions import serializers as drf_serializers

from .models import CommentModel


class CommentSerializer(drf_serializers.PartialUpdateSerializerMixin,
                        serializers.ModelSerializer):
    class Meta:
        model = CommentModel
        fields = (
            'user',
            'title',
            'text',
            'attachment'
        )