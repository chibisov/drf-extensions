from django.urls import re_path

from .views import HelloView


urlpatterns = [
    re_path(r'^hello/$', HelloView.as_view(), name='hello'),
]
