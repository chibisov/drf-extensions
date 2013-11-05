### DRF-extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework).
Source repository is available at [https://github.com/chibisov/drf-extensions](https://github.com/chibisov/drf-extensions).


### Viewsets

Extensions for [viewsets](http://django-rest-framework.org/api-guide/viewsets.html).

#### DetailSerializerMixin

This mixin lets add custom serializer for detail view. Just add mixin and specify `serializer_detail_class` attribute:

    from django.contrib.auth.models import User
    from myapps.serializers import UserSerializer, UserDetailSerializer
    from rest_framework_extensions.mixins import DetailSerializerMixin

    class UserViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
        serializer_class = UserSerializer
        serializer_detail_class = UserDetailSerializer
        queryset = User.objects.all()

Sometimes you need to set custom QuerySet for detail view. For example, in detail view you want to show user groups and permissions for these groups. You can make it by specifying `queryset_detail` attribute:

    from django.contrib.auth.models import User
    from myapps.serializers import UserSerializer, UserDetailSerializer
    from rest_framework_extensions.mixins import DetailSerializerMixin

    class UserViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
        serializer_class = UserSerializer
        serializer_detail_class = UserDetailSerializer
        queryset = User.objects.all()
        queryset_detail = queryset.prefetch_related('groups__permissions')

If you use `DetailSerializerMixin` and don't specify `serializer_detail_class` attribute, then `serializer_class` will be used.

If you use `DetailSerializerMixin` and don't specify `queryset_detail` attribute, then `queryset` will be used.


### Routers

Extensions for [routers](http://django-rest-framework.org/api-guide/routers.html).

You will need to use custom `ExtendedDefaultRouter` or `ExtendedSimpleRouter` for routing if you want to take andantages of described extensions. For example you have standard implementation:

    from rest_framework.routers import DefaultRouter
    router = DefaultRouter()

You should replace `DefaultRouter` with `ExtendedDefaultRouter`:

    from rest_framework_extensions.routers import (
        ExtendedDefaultRouter as DefaultRouter
    )
    router = DefaultRouter()

Or `SimpleRouter` with `ExtendedSimpleRouter`:

    from rest_framework_extensions.routers import (
        ExtendedSimpleRouter as SimpleRouter
    )
    router = SimpleRouter()

#### Collection level controllers

Out of the box Django Rest Framework has controller functionality for detail views. For example:

    from django.contrib.auth.models import User
    from rest_framework import viewsets
    from rest_framework.decorators import action, link
    from rest_framework.response import Response
    from myapp.serializers import UserSerializer

    class UserViewSet(viewsets.ModelViewSet):
        """
        A viewset that provides the standard actions
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

        @action()
        def set_password(self, request, pk=None):
            return Response(['password changed'])

        @link()
        def groups(self, request, pk=None):
            return Response(['user groups'])

Change password request:

    curl -X POST http://127.0.0.1:8000/users/1/set_password/

    ['password changed']

User groups request:

    curl http://127.0.0.1:8000/users/1/groups/
    
    ['user groups']

But what if you want to add custom controller to collection level? 

DRF-extensions `action` and `link` decorators will help you with it. These decorators behaves exactly as default, but can receive additional parameter `is_for_list`:

    ...
    from rest_framework_extensions.decorators import action, link
    ...

    class UserViewSet(viewsets.ModelViewSet):
        """
        A viewset that provides the standard actions
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

        @action(is_for_list=True)
        def confirm_email(self, request, pk=None):
            return Response(['email confirmed'])

        @link(is_for_list=True)
        def surname_first_letters(self, request, pk=None):
            return Response(['a', 'b', 'c'])

        @action()
        def set_password(self, request, pk=None):
            return Response(['password changed'])

        @link()
        def groups(self, request, pk=None):
            return Response(['user groups'])

Now you can post to collection level controller:

    curl http://127.0.0.1:8000/users/confirm_email/ -d "code=123456"
    
    ['email confirmed']

Or retreive data from link collection level controller:

    curl http://127.0.0.1:8000/users/surname_first_letters/
    
    ['a', 'b', 'c']

#### Controller endpoint name

By default function name will be used as name for url routing:

    curl -X POST http://127.0.0.1:8000/users/1/set_password/

    ['password changed']

But what if you want to specify custom name in url. For example `set-password`.

DRF-extensions `action` and `link` decorators will help you to specify custom enpoint name. These decorators behaves exactly as default, but can receive additional parameter `endpoint`:

    ...
    from rest_framework_extensions.decorators import action, link
    ...

    class UserViewSet(viewsets.ModelViewSet):
        """
        A viewset that provides the standard actions
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

        @action(endpoint='set-password')
        def set_password(self, request, pk=None):
            return Response(['password changed'])

Change password request:

    curl -X POST http://127.0.0.1:8000/users/1/set-password/

    ['password changed']


### Change Log

*Nov. 5, 2013*

* Moved docs from readme to github pages
* Docs generation with [Backdoc](https://github.com/chibisov/backdoc)