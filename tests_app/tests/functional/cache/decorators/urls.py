from django.conf.urls import url

from .views import HelloView


urlpatterns = [
    url(r'^hello/$', HelloView.as_view(), name='hello'),
]
