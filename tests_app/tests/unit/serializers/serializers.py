from rest_framework import serializers
from rest_framework_extensions import serializers as drf_serializers

from .models import CommentModel, UserModel


class UserSerializer(drf_serializers.PartialUpdateSerializerMixin,
                     serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'name',
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
            'title_from_source'
        )


class CommentTextSerializer(drf_serializers.PartialUpdateSerializerMixin,
                            serializers.ModelSerializer):

    class Meta:
        model = CommentModel
        fields = (
            'title',
            'text'
        )


class CommentSerializerWithGroupedFields(CommentSerializer):
    text_content = CommentTextSerializer(source='*')

    class Meta(CommentSerializer.Meta):
        fields = (
            'id',
            'user',
            'users_liked',
            'attachment',
            'title_from_source',
            'text_content'
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
