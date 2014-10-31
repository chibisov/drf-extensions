# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import HelloView, HelloParamView


urlpatterns = [
    url(r'^hello/$', HelloView.as_view(), name='hello'),
    url(r'^hello-param/$', HelloParamView.as_view(), name='hello-param'),
]
