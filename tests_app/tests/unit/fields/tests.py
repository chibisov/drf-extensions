import time

from rest_framework import serializers
from rest_framework_extensions.fields import (
    CryptoBinaryField,
    CryptoCharField,
)
import datetime
from django.test import TestCase
from django.conf import settings

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_PASSWORD = b"Non_nobis1solum?nati!sumus"
DEFAULT_SALT = settings.SECRET_KEY


def _generate_password_key(salt=DEFAULT_SALT, password=DEFAULT_PASSWORD):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_to_bytes(salt),
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(_to_bytes(password)))
    return key


def _to_bytes(v):
    if isinstance(v, str):
        return v.encode("utf-8")

    if isinstance(v, bytes):
        return v



def _encrypt(token, value_in_str):
    b_message = value_in_str.encode("utf-8")
    encrypted_message = token.encrypt(b_message)
    return encrypted_message


def _decrypt(token, value, ttl=None):
    ttl = int(ttl) if ttl else None
    decrypted_message = token.decrypt(_to_bytes(value), ttl)
    return decrypted_message.decode("utf-8")


class SaveCrypto(object):
    def __init__(self, message=None, created=None):
        self.message = message
        self.created = created or datetime.datetime.now()


class CryptoSerializer(serializers.Serializer):
    message = CryptoBinaryField(required=False)
    created = serializers.DateTimeField()

    def update(self, instance, validated_data):
        instance.message = validated_data["message"]
        return instance

    def create(self, validated_data):
        return SaveCrypto(**validated_data)


class CryptoCharSerializer(serializers.Serializer):
    message = CryptoCharField(required=False)
    created = serializers.DateTimeField()


class SaltCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(salt="Salt")
    created = serializers.DateTimeField()


class PasswordCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(password="Password")
    created = serializers.DateTimeField()


class TtlCryptoSerializerSerializer(CryptoSerializer):
    message = CryptoBinaryField(ttl=1)
    created = serializers.DateTimeField()


class TestPointSerializer(TestCase):
    def test_create(self):
        """
        Test for creating CryptoBinaryField
        """
        now = datetime.datetime.now()
        message = "test message"
        serializer = CryptoSerializer(data={"created": now, "message": message})
        model_data = SaveCrypto(message=message, created=now)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["created"], model_data.created)
        self.assertFalse(serializer.validated_data is model_data)
        self.assertIs(type(serializer.validated_data["message"]), bytes)

    def test_create_char(self):
        """
        Test for creating CryptoCharField
        """
        now = datetime.datetime.now()
        message = "test message"
        serializer = CryptoCharSerializer(data={"created": now, "message": message})
        model_data = SaveCrypto(message=message, created=now)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["created"], model_data.created)
        self.assertFalse(serializer.validated_data is model_data)
        self.assertIs(type(serializer.validated_data["message"]), str)

    def test_serialization(self):
        """
        Regular JSON serialization should output float values
        """
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = CryptoSerializer(model_data)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_salt(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key("Salt", DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = SaltCryptoSerializerSerializer(model_data)
        time.sleep(3)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_password(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, "Password")
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = PasswordCryptoSerializerSerializer(model_data)
        time.sleep(3)
        self.assertEqual(serializer.data["message"], message)

    def test_serialization_ttl(self):
        now = datetime.datetime.now()
        message = "test message"
        key = _generate_password_key(DEFAULT_SALT, DEFAULT_PASSWORD)
        token = Fernet(key)
        encrypted_message = _encrypt(token, message)
        model_data = SaveCrypto(message=encrypted_message, created=now)
        serializer = TtlCryptoSerializerSerializer(model_data)
        time.sleep(3)
        self.assertEqual(serializer.data["message"], None)
