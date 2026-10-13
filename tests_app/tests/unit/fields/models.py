from django.db import models
from django.utils.translation import gettext_lazy as _

class Address(models.Model):
    postal_code = models.CharField(
        max_length=20, unique=True, verbose_name=_("Postal Code")
    )
    province = models.CharField(max_length=100, verbose_name=_("Province"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    street = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Street")
    )
    additional_info = models.TextField(
        verbose_name=_("Additional Info"), blank=True, null=True
    )