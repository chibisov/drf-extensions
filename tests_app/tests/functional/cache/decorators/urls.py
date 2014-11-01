# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import HelloView, HelloParamView, HelloUserView


urlpatterns = [
    url(r'^hello/$', HelloView.as_view(), name='hello'),
    url(r'^hello-param/$', HelloParamView.as_view(), name='hello-param'),
    url(r'^hello-user/$', HelloUserView.as_view(), name='hello-user'),
]
