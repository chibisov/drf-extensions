from django.urls import re_path

from .views import MyView


urlpatterns = [
    re_path(r'^remove-etag-gzip-postfix/$', MyView.as_view()),
]
