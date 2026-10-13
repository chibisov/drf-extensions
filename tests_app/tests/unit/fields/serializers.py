from rest_framework import serializers

from rest_framework_extensions.fields import FlexibleField, SerializedRelatedField

from .models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

