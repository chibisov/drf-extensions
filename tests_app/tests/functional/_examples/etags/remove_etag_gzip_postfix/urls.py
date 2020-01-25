from django.conf.urls import url

from .views import MyView


urlpatterns = [
    url(r'^remove-etag-gzip-postfix/$', MyView.as_view()),
]
