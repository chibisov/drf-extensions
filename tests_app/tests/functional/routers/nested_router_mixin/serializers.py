from rest_framework import serializers

from .models import (
    NestedRouterMixinUserModel as UserModel,
    NestedRouterMixinGroupModel as GroupModel,
    NestedRouterMixinPermissionModel as PermissionModel,
    NestedRouterMixinTaskModel as TaskModel,
    NestedRouterMixinBookModel as BookModel,
    NestedRouterMixinCommentModel as CommentModel,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'id',
            'name'
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupModel
        fields = (
            'id',
            'name'
        )


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionModel
        fields = (
            'id',
            'name'
        )


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskModel
        fields = (
            'id',
            'title'
        )


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookModel
        fields = (
            'id',
            'title'
        )


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentModel
        fields = (
            'id',
            'content_type',
            'object_id',
            'text'
        )