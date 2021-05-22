from rest_framework.relations import HyperlinkedRelatedField
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

EMPTY_VALUES = (None, "", [], (), {})
DEFAULT_PASSWORD = b"Non_nobis1solum?nati!sumus"
DEFAULT_SALT = settings.SECRET_KEY


class ResourceUriField(HyperlinkedRelatedField):
    """
    Represents a hyperlinking uri that points to the
    detail view for that object.

    Example:
        class SurveySerializer(serializers.ModelSerializer):
            resource_uri = ResourceUriField(view_name='survey-detail')

            class Meta:
                model = Survey
                fields = ('id', 'resource_uri')

        ...
        {
            "id": 1,
            "resource_uri": "http://localhost/v1/surveys/1/",
        }
    """

    # todo: test me
    read_only = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("source", "*")
        super().__init__(*args, **kwargs)


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

    raise TypeError(
        _(
            "SALT & PASSWORD must be specified as strings that convert nicely to "
            "bytes."
        )
    )


def _encrypt(token, value_in_str):
    b_message = value_in_str.encode("utf-8")
    encrypted_message = token.encrypt(b_message)
    return encrypted_message


def _decrypt(token, value, ttl=None):
    ttl = int(ttl) if ttl else None
    decrypted_message = token.decrypt(_to_bytes(value), ttl)
    return decrypted_message.decode("utf-8")


class CryptoBinaryField(serializers.Field):
    """
    A django-rest-framework field for handling encryption through serialisation, where input are string
    and internal python representation is Binary object.

    """

    type_name = "CryptoBinaryField"
    type_label = "crypto"

    default_error_messages = {
        "invalid": _("Input a valid data"),
    }

    def __init__(self, *args, **kwargs):
        self.salt = kwargs.pop("salt", DEFAULT_SALT)
        self.password = kwargs.pop("password", DEFAULT_PASSWORD)
        self.ttl = kwargs.pop("ttl", None)
        super(CryptoBinaryField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """
        Parse json data and return a point object
        """
        if value in EMPTY_VALUES and not self.required:
            return None

        if isinstance(value, str):
            key = _generate_password_key(self.salt, self.password)
            token = Fernet(key)
            encrypted_message = _encrypt(token, value)
            return encrypted_message

        self.fail("invalid")

    def to_representation(self, value):
        """
        Transform POINT object to json.
        """
        if value is None:
            return value
        if isinstance(value, str):
            value = value.encode("utf-8")
        elif isinstance(value, (bytearray, memoryview)):
            value = bytes(value)
        if isinstance(value, bytes):
            key = _generate_password_key(self.salt, self.password)
            token = Fernet(key)
            try:
                decrypted_message = _decrypt(token, value, self.ttl)
                return decrypted_message
            except InvalidToken:
                return None

        self.fail("invalid")


class CryptoCharField(CryptoBinaryField):
    """
    A django-rest-framework field for handling encryption through serialisation, where input are string
    and internal python representation is String object.
    """

    type_name = "CryptoCharField"

    def to_internal_value(self, value):
        value = super(CryptoCharField, self).to_internal_value(value)
        if value:
            return value.decode("utf-8")
        self.fail("invalid")
