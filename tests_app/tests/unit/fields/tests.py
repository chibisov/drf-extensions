
from django.test import TestCase
from decimal import Decimal
from .models import Address
from .serializers import *
from datetime import datetime
from django.utils import timezone
from rest_framework import serializers

class SerializedRelatedFieldTests(TestCase):

    class OrderSerializerPostalCode(serializers.Serializer):
        address = SerializedRelatedField(
            serializer_class=AddressSerializer,
            queryset=Address.objects.all(),
            lookup_field='postal_code',
        )

    class OrderSerializerCity(serializers.Serializer):
        address = SerializedRelatedField(
            serializer_class=AddressSerializer,
            queryset=Address.objects.all(),
            lookup_field='city',
        )

    class OrderSerializerPK(serializers.Serializer):
        address = SerializedRelatedField(
            serializer_class=AddressSerializer,
            queryset=Address.objects.all(),
        )

    def setUp(self):
        self.address = Address.objects.create(
            postal_code="12345",
            province="Tehran",
            city="Tehran",
            street="Valiasr",
            additional_info="Test info"
        )
        Address.objects.create(
            postal_code="123456",
            province="Tehran",
            city="Tehran",
            street="Valiasr",
            additional_info="Test info"
        )

    def test_write_slug(self):
        data = {"address": self.address.postal_code}
        serializer = self.OrderSerializerPostalCode(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["address"] == self.address

    def test_read_nested(self):
        data = {"address": self.address.postal_code}
        serializer = self.OrderSerializerPostalCode(data=data)
        assert serializer.is_valid(), serializer.errors
        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

    def test_write_default(self):
        data = {"address": self.address.pk}
        serializer = self.OrderSerializerPK(data=data)
        assert serializer.is_valid(), serializer.errors
        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

    def test_read_default(self):
        data = {"address": self.address.pk}
        serializer = self.OrderSerializerPK(data=data)
        assert serializer.is_valid(), serializer.errors
        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

    def test_duplicated(self):
        data = {"address": "Tehran"}
        serializer = self.OrderSerializerCity(data=data)
        with self.assertRaises(Address.MultipleObjectsReturned) as exc_info:
            serializer.is_valid(raise_exception=True)
            assert "returned more than one Address -- it returned 2!" in str(exc_info.value)

    def test_not_fount(self):
        data = {"address": "Isfahan"}
        serializer = self.OrderSerializerCity(data=data)
        serializer.is_valid()
        assert "Object with city=Isfahan does not exist." in serializer.errors["address"]


class FlexibleFieldTests(TestCase):

    class OrderSerializerPostalCode(serializers.Serializer):
        address = FlexibleField(
            read=AddressSerializer(),
            write=serializers.SlugRelatedField(
                slug_field="postal_code",
                queryset=Address.objects.all(),
            ),
        )

    class OrderSerializerPK(serializers.Serializer):
        address = FlexibleField(
            read=AddressSerializer(),
            write=serializers.PrimaryKeyRelatedField(
                queryset=Address.objects.all(),
            ),
        )

    class OrderSerializerReadSlug(serializers.Serializer):
        address = FlexibleField(
            read=serializers.SlugRelatedField(
                slug_field="postal_code",
                read_only=True,
            ),
            write=serializers.PrimaryKeyRelatedField(
                queryset=Address.objects.all(),
            ),
        )

    class OrderSerializerNestedWrite(serializers.Serializer):
        address = FlexibleField(
            read=AddressSerializer(),
            write=serializers.SlugRelatedField(
                slug_field="postal_code",
                queryset=Address.objects.all(),
            ),
        )

    class OrderSerializerReadOnly(serializers.Serializer):
        address = FlexibleField(
            read=AddressSerializer(),
        )

    class OrderSerializerWriteOnly(serializers.Serializer):
        address = FlexibleField(
            write=serializers.PrimaryKeyRelatedField(
                queryset=Address.objects.all(),
            ),
        )

    def setUp(self):
        self.address = Address.objects.create(
            postal_code="12345",
            province="Tehran",
            city="Tehran",
            street="Valiasr",
            additional_info="Test info",
        )
        Address.objects.create(
            postal_code="123456",
            province="Tehran",
            city="Tehran",
            street="Valiasr",
            additional_info="Test info",
        )

    def test_write_slug(self):
        data = {"address": self.address.postal_code}
        serializer = self.OrderSerializerPostalCode(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["address"] == self.address

    def test_read_nested(self):
        serializer = self.OrderSerializerPostalCode(
            instance={"address": self.address},
        )

        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

    def test_write_default(self):
        data = {"address": self.address.pk}
        serializer = self.OrderSerializerPK(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["address"] == self.address

    def test_read_default(self):
        serializer = self.OrderSerializerPK(
            instance={"address": self.address},
        )

        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

    def test_read_slug(self):
        serializer = self.OrderSerializerReadSlug(
            instance={"address": self.address},
        )

        assert serializer.data["address"] == self.address.postal_code

    def test_read_slug_data(self):
        data = {
            "address": self.address.pk
        }
        serializer = self.OrderSerializerReadSlug(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.data["address"] == self.address.postal_code

    def test_write_nested(self):
        data = {
            "address": self.address.postal_code
        }
        serializer = self.OrderSerializerNestedWrite(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.data["address"] == AddressSerializer(self.address).data

    def test_invalid_write_slug(self):
        data = {"address": "Isfahan"}
        serializer = self.OrderSerializerPostalCode(data=data)

        assert not serializer.is_valid()
        assert "address" in serializer.errors

    def test_read_only(self):
        serializer = self.OrderSerializerReadOnly(
            instance={"address": self.address},
        )

        expected = AddressSerializer(self.address).data
        assert serializer.data["address"] == expected

        input_serializer = self.OrderSerializerReadOnly(
            data={"address": {"postal_code": "654321"}},
        )

        assert input_serializer.is_valid(), input_serializer.errors
        assert "address" not in input_serializer.validated_data

    def test_write_only(self):
        serializer = self.OrderSerializerWriteOnly(
            data={"address": self.address.pk},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["address"] == self.address

        output_serializer = self.OrderSerializerWriteOnly(
            instance={"address": self.address},
        )

        assert "address" not in output_serializer.data

    def test_requires_read_or_write(self):
        with self.assertRaises(AssertionError):
            FlexibleField()

    def test_different_read_and_write_formats(self):
        class FlexibleSerializer(serializers.Serializer):
            amount = FlexibleField(
                read=serializers.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    coerce_to_string=True,
                ),
                write=serializers.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    coerce_to_string=False,
                ),
            )

        serializer = FlexibleSerializer(data={"amount": "12.50"})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["amount"] == Decimal("12.50")

        output = FlexibleSerializer(instance={"amount": Decimal("12.50")})
        assert output.data["amount"] == "12.50"

    def test_simple_input_and_structured_output(self):
        class CoordinatesSerializer(serializers.Serializer):
            latitude = serializers.FloatField()
            longitude = serializers.FloatField()

        class FlexibleSerializer(serializers.Serializer):
            location = FlexibleField(
                read=CoordinatesSerializer(),
                write=serializers.ListField(
                    child=serializers.FloatField(),
                    min_length=2,
                    max_length=2,
                ),
            )

        serializer = FlexibleSerializer(
            data={"location": [35.7, 51.4]}
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["location"] == [35.7, 51.4]

        output = FlexibleSerializer(
            instance={"location": {"latitude": 35.7, "longitude": 51.4}}
        )
        assert output.data["location"] == {
            "latitude": 35.7,
            "longitude": 51.4,
        }

    def test_write_field_validation(self):
        class FlexibleSerializer(serializers.Serializer):
            amount = FlexibleField(
                read=serializers.CharField(),
                write=serializers.IntegerField(min_value=1),
            )

        serializer = FlexibleSerializer(data={"amount": 0})

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_read_field_representation(self):
        class FlexibleSerializer(serializers.Serializer):
            amount = FlexibleField(
                read=serializers.CharField(),
                write=serializers.IntegerField(),
            )

        serializer = FlexibleSerializer(instance={"amount": 42})

        assert serializer.data["amount"] == "42"

    def test_different_datetime_input_and_output_formats(self):
        class FlexibleSerializer(serializers.Serializer):
            created_at = FlexibleField(
                read=serializers.DateTimeField(
                    format="%Y-%m-%d",
                ),
                write=serializers.DateTimeField(
                    input_formats=["%d/%m/%Y"],
                ),
            )

        serializer = FlexibleSerializer(
            data={"created_at": "12/10/2026"}
        )
        assert serializer.is_valid(), serializer.errors


        assert serializer.validated_data["created_at"].date() == datetime(2026, 10, 12).date()

        output = FlexibleSerializer(
            instance={
                "created_at": serializer.validated_data["created_at"]
            }
        )
        assert output.data["created_at"] == "2026-10-12"
