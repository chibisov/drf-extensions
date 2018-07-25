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


#### PaginateByMaxMixin

*New in DRF-extensions 0.2.2*

This mixin allows to paginate results by [max\_paginate\_by](http://www.django-rest-framework.org/api-guide/pagination#pagination-in-the-generic-views)
value. This approach is useful when clients want to take as much paginated data as possible,
but don't want to bother about backend limitations.

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.mixins import PaginateByMaxMixin

    class UserViewSet(PaginateByMaxMixin,
                      viewsets.ReadOnlyModelViewSet):
        max_paginate_by = 100
        serializer_class = UserSerializer

And now you can send requests with `?page_size=max` argument:

    # Request
    GET /users/?page_size=max HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    {
        count: 1000,
        next: "https://localhost:8000/v1/users/?page=2&page_size=max",
        previous: null,
        results: [
            ...100 items...
        ]
    }

This mixin could be used only with Django Rest Framework >= 2.3.8, because
[max\_paginate\_by](http://www.django-rest-framework.org/topics/release-notes#238)
was introduced in 2.3.8 version.


#### Cache/ETAG mixins

**ReadOnlyCacheResponseAndETAGMixin**

This mixin combines `ReadOnlyETAGMixin` and `CacheResponseMixin`. It could be used with
[ReadOnlyModelViewSet](http://www.django-rest-framework.org/api-guide/viewsets.html#readonlymodelviewset) and helps
to process caching + etag calculation for `retrieve` and `list` methods:

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.mixins import (
        ReadOnlyCacheResponseAndETAGMixin
    )

    class UserViewSet(ReadOnlyCacheResponseAndETAGMixin,
                      viewsets.ReadOnlyModelViewSet):
        serializer_class = UserSerializer

**CacheResponseAndETAGMixin**

This mixin combines `ETAGMixin` and `CacheResponseMixin`. It could be used with
[ModelViewSet](http://www.django-rest-framework.org/api-guide/viewsets.html#modelviewset) and helps
to process:

* Caching for `retrieve` and `list` methods
* Etag for `retrieve`, `list`, `update` and `destroy` methods

Usage:

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.mixins import CacheResponseAndETAGMixin

    class UserViewSet(CacheResponseAndETAGMixin,
                      viewsets.ModelViewSet):
        serializer_class = UserSerializer

Please, read more about [caching](#caching), [key construction](#key-constructor) and [conditional requests](#conditional-requests).


### Routers

Extensions for [routers](http://django-rest-framework.org/api-guide/routers.html).

You will need to use custom `ExtendedDefaultRouter` or `ExtendedSimpleRouter` for routing if you want to take advantages of described extensions. For example you have standard implementation:

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

#### Pluggable router mixins

*New in DRF-extensions 0.2.4*

Every feature in extended routers has it's own mixin. That means that you can use the only features you need in your custom
routers. `ExtendedRouterMixin` has all set of drf-extensions features. For example you can use it with third-party routes:

    from rest_framework_extensions.routers import ExtendedRouterMixin
    from third_party_app.routers import SomeRouter

    class ExtendedSomeRouter(ExtendedRouterMixin, SomeRouter):
        pass

### Nested routes

*New in DRF-extensions 0.2.4*

Nested routes allows you create nested resources with [viewsets](http://www.django-rest-framework.org/api-guide/viewsets.html).

For example:

    from rest_framework_extensions.routers import ExtendedSimpleRouter
    from yourapp.views import (
        UserViewSet,
        GroupViewSet,
        PermissionViewSet,
    )

    router = ExtendedSimpleRouter()
    (
        router.register(r'users', UserViewSet, base_name='user')
              .register(r'groups',
                        GroupViewSet,
                        base_name='users-group',
                        parents_query_lookups=['user_groups'])
              .register(r'permissions',
                        PermissionViewSet,
                        base_name='users-groups-permission',
                        parents_query_lookups=['group__user', 'group'])
    )
    urlpatterns = router.urls

There is one requirement for viewsets which used in nested routers. They should add mixin `NestedViewSetMixin`. That mixin
adds automatic filtering by parent lookups:

    # yourapp.views
    from rest_framework_extensions.mixins import NestedViewSetMixin

    class UserViewSet(NestedViewSetMixin, ModelViewSet):
        model = UserModel

    class GroupViewSet(NestedViewSetMixin, ModelViewSet):
        model = GroupModel

    class PermissionViewSet(NestedViewSetMixin, ModelViewSet):
        model = PermissionModel


With such kind of router we have next resources:

* `/users/` - list of all users. Resolve name is **user-list**
* `/users/<pk>/` - user detail. Resolve name is **user-detail**
* `/users/<parent_lookup_user_groups>/groups/` - list of groups for exact user.
Resolve name is **users-group-list**
* `/users/<parent_lookup_user_groups>/groups/<pk>/` - user group detail. If user doesn't have group then resource will
be not found. Resolve name is **users-group-detail**
* `/users/<parent_lookup_group__user>/groups/<parent_lookup_group>/permissions/` - list of permissions for user group.
Resolve name is **users-groups-permission-list**
* `/users/<parent_lookup_group__user>/groups/<parent_lookup_group>/permissions/<pk>/` - user group permission detail.
If user doesn't have group or group doesn't have permission then resource will be not found.
Resolve name is **users-groups-permission-detail**

Every resource is automatically filtered by parent lookups.

    # Request
    GET /users/1/groups/2/permissions/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8


    [
      {
        id: 3,
        name: "read"
      },
      {
        id: 4,
        name: "update"
      },
      {
        id: 5,
        name: "delete"
      }
    ]

For request above permissions will be filtered by user with pk `1` and group with pk `2`:

    Permission.objects.filter(group__user=1, group=2)

Example with registering more then one nested resource in one depth:

    permissions_routes = router.register(
        r'permissions',
        PermissionViewSet,
        base_name='permission'
    )
    permissions_routes.register(
        r'groups',
        GroupViewSet,
        base_name='permissions-group',
        parents_query_lookups=['permissions']
    )
    permissions_routes.register(
        r'users',
        UserViewSet,
        base_name='permissions-user',
        parents_query_lookups=['groups__permissions']
    )

With such kind of router we have next resources:

* `/permissions/` - list of all permissions. Resolve name is **permission-list**
* `/permissions/<pk>/` - permission detail. Resolve name is **permission-detail**
* `/permissions/<parent_lookup_permissions>/groups/` - list of groups for exact permission.
Resolve name is **permissions-group-list**
* `/permissions/<parent_lookup_permissions>/groups/<pk>/` - permission group detail. If group doesn't have
permission then resource will be not found. Resolve name is **permissions-group-detail**
* `/permissions/<parent_lookup_groups__permissions>/users/` - list of users for exact permission.
Resolve name is **permissions-user-list**
* `/permissions/<parent_lookup_groups__permissions>/user/<pk>/` - permission user detail. If user doesn't have
permission then resource will be not found. Resolve name is **permissions-user-detail**

#### Nested router mixin

You can use `rest_framework_extensions.routers.NestedRouterMixin` for adding nesting feature into your routers:

    from rest_framework_extensions.routers import NestedRouterMixin
    from rest_framework.routers import SimpleRouter

    class SimpleRouterWithNesting(NestedRouterMixin, SimpleRouter):
        pass

#### Usage with generic relations

If you want to use nested router for [generic relation](https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/#generic-relations)
fields, you should explicitly filter `QuerySet` by content type.

For example if you have such kind of models:

    class Task(models.Model):
        title = models.CharField(max_length=30)

    class Book(models.Model):
        title = models.CharField(max_length=30)

    class Comment(models.Model):
        content_type = models.ForeignKey(ContentType)
        object_id = models.PositiveIntegerField()
        content_object = generic.GenericForeignKey()
        text = models.CharField(max_length=30)

Lets create viewsets for that models:

    class TaskViewSet(NestedViewSetMixin, ModelViewSet):
        model = TaskModel

    class BookViewSet(NestedViewSetMixin, ModelViewSet):
        model = BookModel

    class CommentViewSet(NestedViewSetMixin, ModelViewSet):
        queryset = CommentModel.objects.all()

And router like this:

    router = ExtendedSimpleRouter()
    # tasks route
    (
        router.register(r'tasks', TaskViewSet)
              .register(r'comments',
                        CommentViewSet,
                        'tasks-comment',
                        parents_query_lookups=['object_id'])
    )
    # books route
    (
        router.register(r'books', BookViewSet)
              .register(r'comments',
                        CommentViewSet,
                        'books-comment',
                        parents_query_lookups=['object_id'])
    )

As you can see we've added to `parents_query_lookups` only one `object_id` value. But when you make requests to `comments`
endpoint for both tasks and books routes there is no context for current content type.

    # Request
    GET /tasks/123/comments/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    [
        {
            id: 1,
            content_type: 1,
            object_id: 123,
            text: "Good task!"
        },
        {
            id: 2,
            content_type: 2,  // oops. Wrong content type (for book)
            object_id: 123,   // task and book has the same id
            text: "Good book!"
        },
    ]

For such kind of cases you should explicitly filter `QuerySets` of nested viewsets by content type:

    from django.contrib.contenttypes.models import ContentType

    class CommentViewSet(NestedViewSetMixin, ModelViewSet):
        queryset = CommentModel.objects.all()

    class TaskCommentViewSet(CommentViewSet):
        def get_queryset(self):
            return super(TaskCommentViewSet, self).get_queryset().filter(
                content_type=ContentType.objects.get_for_model(TaskModel)
            )

    class BookCommentViewSet(CommentViewSet):
        def get_queryset(self):
            return super(BookCommentViewSet, self).get_queryset().filter(
                content_type=ContentType.objects.get_for_model(BookModel)
            )

Lets use new viewsets in router:

    router = ExtendedSimpleRouter()
    # tasks route
    (
        router.register(r'tasks', TaskViewSet)
              .register(r'comments',
                        TaskCommentViewSet,
                        'tasks-comment',
                        parents_query_lookups=['object_id'])
    )
    # books route
    (
        router.register(r'books', BookViewSet)
              .register(r'comments',
                        BookCommentViewSet,
                        'books-comment',
                        parents_query_lookups=['object_id'])
    )


### Serializers

Extensions for [serializers](http://www.django-rest-framework.org/api-guide/serializers) functionality.

#### PartialUpdateSerializerMixin

*New in DRF-extensions 0.2.3*

By default every saving of [ModelSerializer](http://www.django-rest-framework.org/api-guide/serializers#modelserializer)
saves the whole object. Even partial update just patches model instance. For example:

    from myapps.models import City
    from myapps.serializers import CitySerializer

    moscow = City.objects.get(pk=10)
    city_serializer = CitySerializer(
        instance=moscow,
        data={'country': 'USA'},
        partial=True
    )
    if city_serializer.is_valid():
        city_serializer.save()

    # equivalent to
    moscow.country = 'USA'
    moscow.save()

SQL representation for previous example will be:

    UPDATE city SET name='Moscow', country='USA' WHERE id=1;

Django's `save` method has keyword argument [update_fields](https://docs.djangoproject.com/en/dev/ref/models/instances/#specifying-which-fields-to-save).
Only the fields named in that list will be updated:

    moscow.country = 'USA'
    moscow.save(update_fields=['country'])

SQL representation for example with `update_fields` usage will be:

    UPDATE city SET country='USA' WHERE id=1;

To use `update_fields` for every partial update you should mixin `PartialUpdateSerializerMixin` to your serializer:

    from rest_framework_extensions.serializers import (
        PartialUpdateSerializerMixin
    )

    class CitySerializer(PartialUpdateSerializerMixin,
                         serializers.ModelSerializer):
        class Meta:
            model = City

### Fields

Set of serializer fields that extends [default fields](http://www.django-rest-framework.org/api-guide/fields) functionality.

#### ResourceUriField

Represents a hyperlinking uri that points to the detail view for that object.

    from rest_framework_extensions.fields import ResourceUriField

    class CitySerializer(serializers.ModelSerializer):
        resource_uri = ResourceUriField(view_name='city-detail')

        class Meta:
            model = City

Request example:

    # Request
    GET /cities/268/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    {
      id: 268,
      resource_uri: "http://localhost:8000/v1/cities/268/",
      name: "Serpuhov"
    }


### Permissions

Extensions for [permissions](http://www.django-rest-framework.org/api-guide/permissions.html).

#### Object permissions

*New in DRF-extensions 0.2.2*

Django Rest Framework allows you to use [DjangoObjectPermissions](http://www.django-rest-framework.org/api-guide/permissions#djangoobjectpermissions) out of the box. But it has one limitation - if user has no permissions for viewing resource he will get `404` as response code. In most cases it's good approach because it solves security issues by default. But what if you wanted to return `401` or `403`? What if you wanted to say to user - "You need to be logged in for viewing current resource" or "You don't have permissions for viewing current resource"?

`ExtenedDjangoObjectPermissions` will help you to be more flexible. By default it behaves as standard [DjangoObjectPermissions](http://www.django-rest-framework.org/api-guide/permissions#djangoobjectpermissions). For example, it is safe to replace `DjangoObjectPermissions` with extended permissions class:

    from rest_framework_extensions.permissions import (
        ExtendedDjangoObjectPermissions as DjangoObjectPermissions
    )

    class CommentView(viewsets.ModelViewSet):
        permission_classes = (DjangoObjectPermissions,)

Now every request from unauthorized user will get `404` response:

    # Request
    GET /comments/1/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 404 NOT FOUND
    Content-Type: application/json; charset=UTF-8

    {"detail": "Not found"}

With `ExtenedDjangoObjectPermissions` you can disable hiding forbidden for read objects by changing `hide_forbidden_for_read_objects` attribute:

    from rest_framework_extensions.permissions import (
        ExtendedDjangoObjectPermissions
    )

    class CommentViewObjectPermissions(ExtendedDjangoObjectPermissions):
        hide_forbidden_for_read_objects = False

    class CommentView(viewsets.ModelViewSet):
        permission_classes = (CommentViewObjectPermissions,)

Now lets see request response for user that has no permissions for viewing `CommentView` object:

    # Request
    GET /comments/1/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 403 FORBIDDEN
    Content-Type: application/json; charset=UTF-8

    {u'detail': u'You do not have permission to perform this action.'}

`ExtenedDjangoObjectPermissions` could be used only with Django Rest Framework >= 2.3.8, because [DjangoObjectPermissions](http://www.django-rest-framework.org/topics/release-notes#238) was introduced in 2.3.8 version.


### Caching

To cache something is to save the result of an expensive calculation so that you don't have to perform the calculation next time. Here's some pseudocode explaining how this would work for a dynamically generated api response:

    given a URL, try finding that API response in the cache
    if the response is in the cache:
        return the cached response
    else:
        generate the response
        save the generated response in the cache (for next time)
        return the generated response

#### Cache response

DRF-extensions allows you to cache api responses with simple `@cache_response` decorator.
There are two requirements for decorated method:

* It should be method of class which is inherited from `rest_framework.views.APIView`
* It should return `rest_framework.response.Response` instance.

Usage example:

    from rest_framework.response import Response
    from rest_framework import views
    from rest_framework_extensions.cache.decorators import (
        cache_response
    )
    from myapp.models import City

    class CityView(views.APIView):
        @cache_response()
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)

If you request view first time you'll get it from processed SQL query. (~60ms response time):

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    ['Moscow', 'London', 'Paris']

Second request will hit the cache. No sql evaluation, no database query. (~30 ms response time):

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    ['Moscow', 'London', 'Paris']

Reduction in response time depends on calculation complexity inside your API method. Sometimes it reduces from 1 second to 10ms, sometimes you win just 10ms.

#### Timeout

You can specify cache timeout in seconds, providing first argument:

    class CityView(views.APIView):
        @cache_response(60 * 15)
        def get(self, request, *args, **kwargs):
            ...

In the above example, the result of the `get()` view will be cached for 15 minutes.

If you don't specify `timeout` argument then value from `REST_FRAMEWORK_EXTENSIONS` settings will be used. By default it's `None`, which means "cache forever". You can change this default in settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
    }

#### Usage of the specific cache

*New in DRF-extensions 0.2.3*

`@cache_response` can also take an optional keyword argument, `cache`, which directs the decorator
to use a specific cache (from your [CACHES](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CACHES) setting) when caching results.
By default, the `default` cache will be used, but you can specify any cache you want:

    class CityView(views.APIView):
        @cache_response(60 * 15, cache='special_cache')
        def get(self, request, *args, **kwargs):
            ...

You can specify what cache to use by default in settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_USE_CACHE': 'special_cache'
    }

#### Cache key

By default every cached data from `@cache_response` decorator stored by key, which calculated
with [DefaultKeyConstructor](#default-key-constructor).

You can change cache key by providing `key_func` argument, which must be callable:

    def calculate_cache_key(view_instance, view_method,
                            request, args, kwargs):
        return '.'.join([
            len(args),
            len(kwargs)
        ])

    class CityView(views.APIView):
        @cache_response(60 * 15, key_func=calculate_cache_key)
        def get(self, request, *args, **kwargs):
            ...

You can implement view method and use it for cache key calculation by specifying `key_func` argument as string:

    class CityView(views.APIView):
        @cache_response(60 * 15, key_func='calculate_cache_key')
        def get(self, request, *args, **kwargs):
            ...

        def calculate_cache_key(self, view_instance, view_method,
                                request, args, kwargs):
            return '.'.join([
                len(args),
                len(kwargs)
            ])

Key calculation function will be called with next parameters:

* **view_instance** - view instance of decorated method
* **view_method** - decorated method
* **request** - decorated method request
* **args** - decorated method positional arguments
* **kwargs** - decorated method keyword arguments

#### Default key function

If `@cache_response` decorator used without key argument then default key function will be used. You can change this function in
settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_CACHE_KEY_FUNC':
          'rest_framework_extensions.utils.default_cache_key_func'
    }

`default_cache_key_func` uses [DefaultKeyConstructor](#default-key-constructor) as a base for key calculation.

#### Caching errors

*New in DRF-extensions 0.2.7*

By default every response is cached, even failed. For example:

    class CityView(views.APIView):
        @cache_response()
        def get(self, request, *args, **kwargs):
            raise Exception("500 error comes from here")

First request to `CityView.get` will fail with `500` status code error and next requests to this endpoint will
return `500` error from cache.

You can change this behaviour by turning off caching error responses:

    class CityView(views.APIView):
        @cache_response(cache_errors=False)
        def get(self, request, *args, **kwargs):
            raise Exception("500 error comes from here")

You can change default behaviour by changing `DEFAULT_CACHE_ERRORS` setting:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_CACHE_ERRORS': False
    }

#### CacheResponseMixin

It is common to cache standard [viewset](http://www.django-rest-framework.org/api-guide/viewsets) `retrieve` and `list`
methods. That is why `CacheResponseMixin` exists. Just mix it into viewset implementation and those methods will
use functions, defined in `REST_FRAMEWORK_EXTENSIONS` [settings](#settings):

* *"DEFAULT\_OBJECT\_CACHE\_KEY\_FUNC"* for `retrieve` method
* *"DEFAULT\_LIST\_CACHE\_KEY\_FUNC"* for `list` method

By default those functions are using [DefaultKeyConstructor](#default-key-constructor) and extends it:

* With `RetrieveSqlQueryKeyBit` for *"DEFAULT\_OBJECT\_CACHE\_KEY\_FUNC"*
* With `ListSqlQueryKeyBit` and `PaginationKeyBit` for *"DEFAULT\_LIST\_CACHE\_KEY\_FUNC"*

You can change those settings for custom cache key generation:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_OBJECT_CACHE_KEY_FUNC':
          'rest_framework_extensions.utils.default_object_cache_key_func',
        'DEFAULT_LIST_CACHE_KEY_FUNC':
          'rest_framework_extensions.utils.default_list_cache_key_func',
    }

Mixin example usage:

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.cache.mixins import CacheResponseMixin

    class UserViewSet(CacheResponseMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

You can change cache key function by providing `object_cache_key_func` or
`list_cache_key_func` methods in view class:

    class UserViewSet(CacheResponseMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

        def object_cache_key_func(self, **kwargs):
            return 'some key for object'

        def list_cache_key_func(self, **kwargs):
            return 'some key for list'

Of course you can use custom [key constructor](#key-constructor):

    from yourapp.key_constructors import (
        CustomObjectKeyConstructor,
        CustomListKeyConstructor,
    )

    class UserViewSet(CacheResponseMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer
        object_cache_key_func = CustomObjectKeyConstructor()
        list_cache_key_func = CustomListKeyConstructor()

If you want to cache only `retrieve` method then you could use `rest_framework_extensions.cache.mixins.RetrieveCacheResponseMixin`.

If you want to cache only `list` method then you could use `rest_framework_extensions.cache.mixins.ListCacheResponseMixin`.


### Key constructors

As you could see from previous section cache key calculation might seem fairly simple operation. But let's see next example. We make ordinary HTTP request to cities resource:

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    ['Moscow', 'London', 'Paris']

By the moment all goes fine - response returned and cached. Let's make the same request requiring XML response:

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/xml

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    ['Moscow', 'London', 'Paris']

What is that? Oh, we forgot about format negotiations. We can add format to key bits:

    def calculate_cache_key(view_instance, view_method,
                            request, args, kwargs):
        return '.'.join([
            len(args),
            len(kwargs),
            request.accepted_renderer.format  # here it is
        ])

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/xml

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/xml; charset=UTF-8

    <?xml version="1.0" encoding="utf-8"?>
    <root>
        <list-item>Moscow</list-item>
        <list-item>London</list-item>
        <list-item>Paris</list-item>
    </root>

That's cool now - we have different responses for different formats with different cache keys. But there are many cases, where key should be different for different requests:

* Response format (json, xml);
* User (exact authorized user or anonymous);
* Different request meta data (request.META['REMOTE_ADDR']);
* Language (ru, en);
* Headers;
* Query params. For example, `jsonp` resources need `callback` param, which rendered in response;
* Pagination. We should show different data for different pages;
* Etc...

Of course we can use custom `calculate_cache_key` methods and reuse them for different API methods, but we can't reuse just parts of them. For example, one method depends on user id and language, but another only on user id. How to be more DRYish? Let's see some magic:

    from rest_framework_extensions.key_constructor.constructors import (
        KeyConstructor
    )
    from rest_framework_extensions.key_constructor import bits
    from your_app.utils import get_city_by_ip

    class CityGetKeyConstructor(KeyConstructor):
        unique_method_id = bits.UniqueMethodIdKeyBit()
        format = bits.FormatKeyBit()
        language = bits.LanguageKeyBit()

    class CityHeadKeyConstructor(CityGetKeyConstructor):
        user = bits.UserKeyBit()
        request_meta = bits.RequestMetaKeyBit(params=['REMOTE_ADDR'])

    class CityView(views.APIView):
        @cache_response(key_func=CityGetKeyConstructor())
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)

        @cache_response(key_func=CityHeadKeyConstructor())
        def head(self, request, *args, **kwargs):
            city = ''
            user = self.request.user
            if user.is_authenticated and user.city:
                city = Response(user.city.name)
            if not city:
                city = get_city_by_ip(request.META['REMOTE_ADDR'])
            return Response(city)

Firstly, let's revise `CityView.get` method cache key calculation. It constructs from 3 bits:

* **unique\_method\_id** - remember our [default key calculation](#cache-key)? Here it is. Just one of the cache key bits. `head` method has different set of bits and they can't collide with `get` method bits. But there could be another view class with the same bits.
* **format** - key would be different for different formats.
* **language** - key would be different for different languages.

The second method `head` has the same `unique_method_id`, `format` and `language` bits, buts extends with 2 more:

* **user** - key would be different for different users. As you can see in response calculation we use `request.user` instance. For different users we need different responses.
* **request_meta** - key would be different for different ip addresses. As you can see in response calculation we are falling back to getting city from ip address if couldn't get it from authorized user model.

All default key bits are listed in [this section](#default-key-bits).

#### Default key constructor

`DefaultKeyConstructor` is located in `rest_framework_extensions.key_constructor.constructors` module and constructs a key
from unique *method* id, request format and request language. It has the following implementation:

    class DefaultKeyConstructor(KeyConstructor):
        unique_method_id = bits.UniqueMethodIdKeyBit()
        format = bits.FormatKeyBit()
        language = bits.LanguageKeyBit()

#### How key constructor works

Key constructor class works in the same manner as the standard [django forms](https://docs.djangoproject.com/en/dev/topics/forms/) and
key bits used like form fields. Lets go through key construction steps for [DefaultKeyConstructor](#default-key-constructor).

Firstly, constructor starts iteration over every key bit:

* **unique\_method\_id**
* **format**
* **language**

Then constructor gets data from every key bit calling method `get_data`:

* **unique\_method\_id** - `u'your_app.views.SometView.get'`
* **format** - `u'json'`
* **language** - `u'en'`

Every key bit `get_data` method is called with next arguments:

* **view_instance** - view instance of decorated method
* **view_method** - decorated method
* **request** - decorated method request
* **args** - decorated method positional arguments
* **kwargs** - decorated method keyword arguments

After this it combines every key bit data to one dict, which keys are a key bits names in constructor, and values are returned data:

    {
        'unique_method_id': u'your_app.views.SometView.get',
        'format': u'json',
        'language': u'en'
    }

Then constructor dumps resulting dict to json:

    '{"unique_method_id": "your_app.views.SometView.get", "language": "en", "format": "json"}'

And finally compresses json with **md5** and returns hash value:

    'b04f8f03c89df824e0ecd25230a90f0e0ebe184cf8c0114342e9471dd2275baa'

#### Custom key bit

We are going to create a simple key bit which could be used in real applications with next properties:

* High read rate
* Low write rate

The task is - cache every read request and invalidate all cache data after write to any model, which used in API. This approach
let us don't think about granular cache invalidation - just flush it after any model instance change/creation/deletion.

Lets create models:

    # models.py
    from django.db import models

    class Group(models.Model):
        title = models.CharField()

    class Profile(models.Model):
        name = models.CharField()
        group = models.ForeignKey(Group)

Define serializers:

    # serializers.py
    from yourapp.models import Group, Profile
    from rest_framework import serializers

    class GroupSerializer(serializers.ModelSerializer):
        class Meta:
            model = Group

    class ProfileSerializer(serializers.ModelSerializer):
        group = GroupSerializer()

        class Meta:
            model = Profile

Create views:

    # views.py
    from yourapp.serializers import GroupSerializer, ProfileSerializer
    from yourapp.models import Group, Profile

    class GroupViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = GroupSerializer
        queryset = Group.objects.all()

    class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = ProfileSerializer
        queryset = Profile.objects.all()

And finally register views in router:

    # urls.py
    from yourapp.views import GroupViewSet,ProfileViewSet

    router = DefaultRouter()
    router.register(r'groups', GroupViewSet)
    router.register(r'profiles', ProfileViewSet)
    urlpatterns = router.urls

At the moment we have API, but it's not cached. Lets cache it and create our custom key bit:

    # views.py
    import datetime
    from django.core.cache import cache
    from django.utils.encoding import force_text
    from yourapp.serializers import GroupSerializer, ProfileSerializer
    from rest_framework_extensions.cache.decorators import cache_response
    from rest_framework_extensions.key_constructor.constructors import (
        DefaultKeyConstructor
    )
    from rest_framework_extensions.key_constructor.bits import (
        KeyBitBase,
        RetrieveSqlQueryKeyBit,
        ListSqlQueryKeyBit,
        PaginationKeyBit
    )

    class UpdatedAtKeyBit(KeyBitBase):
        def get_data(self, **kwargs):
            key = 'api_updated_at_timestamp'
            value = cache.get(key, None)
            if not value:
                value = datetime.datetime.utcnow()
                cache.set(key, value=value)
            return force_text(value)

    class CustomObjectKeyConstructor(DefaultKeyConstructor):
        retrieve_sql = RetrieveSqlQueryKeyBit()
        updated_at = UpdatedAtKeyBit()

    class CustomListKeyConstructor(DefaultKeyConstructor):
        list_sql = ListSqlQueryKeyBit()
        pagination = PaginationKeyBit()
        updated_at = UpdatedAtKeyBit()

    class GroupViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = GroupSerializer

        @cache_response(key_func=CustomObjectKeyConstructor())
        def retrieve(self, *args, **kwargs):
            return super(GroupViewSet, self).retrieve(*args, **kwargs)

        @cache_response(key_func=CustomListKeyConstructor())
        def list(self, *args, **kwargs):
            return super(GroupViewSet, self).list(*args, **kwargs)

    class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = ProfileSerializer

        @cache_response(key_func=CustomObjectKeyConstructor())
        def retrieve(self, *args, **kwargs):
            return super(ProfileViewSet, self).retrieve(*args, **kwargs)

        @cache_response(key_func=CustomListKeyConstructor())
        def list(self, *args, **kwargs):
            return super(ProfileViewSet, self).list(*args, **kwargs)

As you can see `UpdatedAtKeyBit` just adds to key information when API models has been update last time. If there is no
information about it then new datetime will be used for key bit data.

Lets write cache invalidation. We just connect models to standard signals and change value in cache by key `api_updated_at_timestamp`:

    # models.py
    import datetime
    from django.db import models
    from django.db.models.signals import post_save, post_delete

    def change_api_updated_at(sender=None, instance=None, *args, **kwargs):
        cache.set('api_updated_at_timestamp', datetime.datetime.utcnow())

    class Group(models.Model):
        title = models.CharField()

    class Profile(models.Model):
        name = models.CharField()
        group = models.ForeignKey(Group)

    for model in [Group, Profile]:
        post_save.connect(receiver=change_api_updated_at, sender=model)
        post_delete.connect(receiver=change_api_updated_at, sender=model)

And that's it. When any model changes then value in cache by key `api_updated_at_timestamp` will be changed too. After this every
key constructor, that used `UpdatedAtKeyBit`, will construct new keys and `@cache_response` decorator will
cache data in new places.

#### Key constructor params

*New in DRF-extensions 0.2.3*

You can change `params` attribute for specific key bit by providing `params` dict for key constructor initialization
function. For example, here is custom key constructor, which inherits from [DefaultKeyConstructor](#default-key-constructor)
and adds geoip key bit:

    class CityKeyConstructor(DefaultKeyConstructor):
        geoip = bits.RequestMetaKeyBit(params=['GEOIP_CITY'])

If you wanted to use `GEOIP_COUNTRY`, you could create new key constructor:

    class CountryKeyConstructor(DefaultKeyConstructor):
        geoip = bits.RequestMetaKeyBit(params=['GEOIP_COUNTRY'])

But there is another way. You can send `params` in key constructor initialization method. This is the dict attribute, where
keys are bit names and values are bit `params` attribute value (look at `CountryView`):

    class CityKeyConstructor(DefaultKeyConstructor):
        geoip = bits.RequestMetaKeyBit(params=['GEOIP_COUNTRY'])

    class CityView(views.APIView):
        @cache_response(key_func=CityKeyConstructor())
        def get(self, request, *args, **kwargs):
            ...

    class CountryView(views.APIView):
        @cache_response(key_func=CityKeyConstructor(
            params={'geoip': ['GEOIP_COUNTRY']}
        ))
        def get(self, request, *args, **kwargs):
            ...

If there is no item provided for key bit then default key bit `params` value will be used.

#### Constructor's bits list

You can dynamically change key constructor's bits list in initialization method by altering `bits` attribute:

    class CustomKeyConstructor(DefaultKeyConstructor):
        def __init__(self, *args, **kwargs):
            super(CustomKeyConstructor, self).__init__(*args, **kwargs)
            self.bits['geoip'] = bits.RequestMetaKeyBit(
                params=['GEOIP_CITY']
            )


### Default key bits

Out of the box DRF-extensions has some basic key bits. They are all located in `rest_framework_extensions.key_constructor.bits` module.

#### FormatKeyBit

Retrieves format info from request. Usage example:

    class MyKeyConstructor(KeyConstructor):
        format = FormatKeyBit()

#### LanguageKeyBit

Retrieves active language for request. Usage example:

    class MyKeyConstructor(KeyConstructor):
        language = LanguageKeyBit()

#### UserKeyBit

Retrieves user id from request. If it is anonymous then returnes *"anonymous"* string. Usage example:

    class MyKeyConstructor(KeyConstructor):
        user = UserKeyBit()

#### RequestMetaKeyBit

Retrieves data from [request.META](https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.META) dict.
Usage example:

    class MyKeyConstructor(KeyConstructor):
        ip_address_and_user_agent = bits.RequestMetaKeyBit(
            ['REMOTE_ADDR', 'HTTP_USER_AGENT']
        )

You can use `*` for retrieving all meta data to key bit:

*New in DRF-extensions 0.2.7*

    class MyKeyConstructor(KeyConstructor):
        all_request_meta = bits.RequestMetaKeyBit('*')

#### HeadersKeyBit

Same as `RequestMetaKeyBit` retrieves data from [request.META](https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.META) dict.
The difference is that `HeadersKeyBit` allows to use normal header names:

    class MyKeyConstructor(KeyConstructor):
        user_agent_and_geobase_id = bits.HeadersKeyBit(
            ['user-agent', 'x-geobase-id']
        )
        # will process request.META['HTTP_USER_AGENT'] and
        #              request.META['HTTP_X_GEOBASE_ID']

You can use `*` for retrieving all headers to key bit:

*New in DRF-extensions 0.2.7*

    class MyKeyConstructor(KeyConstructor):
        all_headers = bits.HeadersKeyBit('*')

#### ArgsKeyBit

*New in DRF-extensions 0.2.7*

Retrieves data from the view's positional arguments.
A list of position indices can be passed to indicate which arguments to use. For retrieving all arguments you can use `*` which is also the default value:

    class MyKeyConstructor(KeyConstructor):
        args = bits.ArgsKeyBit()  # will use all positional arguments

    class MyKeyConstructor(KeyConstructor):
        args = bits.ArgsKeyBit('*')  # same as above

    class MyKeyConstructor(KeyConstructor):
        args = bits.ArgsKeyBit([0, 2])

#### KwargsKeyBit

*New in DRF-extensions 0.2.7*

Retrieves data from the views's keyword arguments.
A list of keyword argument names can be passed to indicate which kwargs to use. For retrieving all kwargs you can use `*` which is also the default value:

    class MyKeyConstructor(KeyConstructor):
        kwargs = bits.KwargsKeyBit()  # will use all keyword arguments

    class MyKeyConstructor(KeyConstructor):
        kwargs = bits.KwargsKeyBit('*')  # same as above

    class MyKeyConstructor(KeyConstructor):
        kwargs = bits.KwargsKeyBit(['user_id', 'city'])

#### QueryParamsKeyBit

Retrieves data from [request.GET](https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.GET) dict.
Usage example:

    class MyKeyConstructor(KeyConstructor):
        part_and_callback = bits.QueryParamsKeyBit(
            ['part', 'callback']
        )

You can use `*` for retrieving all query params to key bit which is also the default value:

*New in DRF-extensions 0.2.7*

    class MyKeyConstructor(KeyConstructor):
        all_query_params = bits.QueryParamsKeyBit('*')  # all qs parameters

    class MyKeyConstructor(KeyConstructor):
        all_query_params = bits.QueryParamsKeyBit()  # same as above

#### PaginationKeyBit

Inherits from `QueryParamsKeyBit` and returns data from used pagination params.

    class MyKeyConstructor(KeyConstructor):
        pagination = bits.PaginationKeyBit()

#### ListSqlQueryKeyBit

Retrieves sql query for `view.filter_queryset(view.get_queryset())` filtering.

    class MyKeyConstructor(KeyConstructor):
        list_sql_query = bits.ListSqlQueryKeyBit()

#### RetrieveSqlQueryKeyBit

Retrieves sql query for retrieving exact object.

    class MyKeyConstructor(KeyConstructor):
        retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()

#### UniqueViewIdKeyBit

Combines data about view module and view class name.

    class MyKeyConstructor(KeyConstructor):
        unique_view_id = bits.UniqueViewIdKeyBit()

#### UniqueMethodIdKeyBit

Combines data about view module, view class name and view method name.

    class MyKeyConstructor(KeyConstructor):
        unique_view_id = bits.UniqueMethodIdKeyBit()

#### ListModelKeyBit

*New in DRF-extensions 0.3.2*

Computes the semantic fingerprint of a list of objects returned by `view.filter_queryset(view.get_queryset())`
using a flat representation of all objects' values.

    class MyKeyConstructor(KeyConstructor):
        list_model_values = bits.ListModelKeyBit()

#### RetrieveModelKeyBit

*New in DRF-extensions 0.3.2*

Computes the semantic fingerprint of a particular objects returned by `view.get_object()`.

    class MyKeyConstructor(KeyConstructor):
        retrieve_model_values = bits.RetrieveModelKeyBit()





### Conditional requests

*This documentation section uses information from [RESTful Web Services Cookbook](http://shop.oreilly.com/product/9780596801694.do) 10-th chapter.*

Conditional HTTP requests allow API clients to accomplish 2 goals:

1. Conditional HTTP GET saves client and server [time and bandwidth](#saving-time-and-bandwidth).
* For unsafe requests such as PUT, POST, and DELETE, conditional requests provide [concurrency control](#concurrency-control).

The second goal addresses the lost update problem, where a resource is altered and saved by user B while user A is still editing.
In both cases, the 'condition' included in the request needs to be a unique identifier (e.g. unique semantic fingerprint) of the requested resource in order to detect changes.
This fingerprint can be transient (i.e. using the cache as with `UpdatedAtKeyBit`), or persistent, i.e. computed from the model instance attribute values from the database. 
While the `UpdatedAtKeyBit` approach requires to add triggers to your models, the semantic fingerprint option is designed to be pluggable and does not require to alter your model code. 


#### HTTP ETag

*An ETag or entity tag, is part of HTTP, the protocol for the World Wide Web. 
It is one of several mechanisms that HTTP provides for web cache validation, and which allows a client to make conditional requests.* - [Wikipedia](http://en.wikipedia.org/wiki/HTTP_ETag)

For ETag calculation and conditional request processing you should use the decorators from `rest_framework_extensions.etag.decorators`.
The `@etag` decorator works similar to the native [django decorator](https://docs.djangoproject.com/en/dev/topics/conditional-view-processing/).

<!-- THIS REFERS TO THE DEFAULT_OBJ_ETAG_FUNC -->
The [default ETag function](#default-etag-function) used by the `@etag` decorator computes the value with respect to the particular view and HTTP method in the request and therefore *cannot detect changes in individual model instances*.
If you need to compute the *semantic* fingerprint of a model independent of a particular view and method, implement your custom `etag_func`.
Alternatively you could use the `@api_etag` decorator and specify the `viewset` in the view.


    from rest_framework_extensions.etag.decorators import etag

    class CityView(views.APIView):
        @etag()
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)

By default `@etag` would calculate the ETag header value with the same algorithm as [cache key](#cache-key) default calculation performs.

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8
    ETag: "e7b50490dc546d116635a14cfa58110306dd6c5434146b6740ec08bf0a78f9a2"

    ['Moscow', 'London', 'Paris']

You can define a custom function for Etag value calculation with `etag_func` argument:

    from rest_framework_extensions.etag.decorators import etag

    def calculate_etag(view_instance, view_method,
                       request, args, kwargs):
        return '.'.join([
            len(args),
            len(kwargs)
        ])

    class CityView(views.APIView):
        @etag(etag_func=calculate_etag)
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)


You can implement a view method and use it for Etag calculation by specifying `etag_func` argument as string:

    from rest_framework_extensions.etag.decorators import etag

    class CityView(views.APIView):
        @etag(etag_func='calculate_etag_from_method')
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)

        def calculate_etag_from_method(self, view_instance, view_method,
                                       request, args, kwargs):
            return '.'.join([
                len(args),
                len(kwargs)
            ])

ETag calculation function will be called with following parameters:

* **view_instance** - view instance of decorated method
* **view_method** - decorated method
* **request** - decorated method request
* **args** - decorated method positional arguments
* **kwargs** - decorated method keyword arguments


#### Default ETag function

If `@etag` decorator used without `etag_func` argument then default etag function will be used. You can change this function in
settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_ETAG_FUNC':
          'rest_framework_extensions.utils.default_etag_func'
    }

`default_etag_func` uses [DefaultKeyConstructor](#default-key-constructor) as a base for etag calculation.


#### API ETag function
<!-- This refers to the APIETagProcessor and @api_etag decorator -->

*New in DRF-extensions 0.3.2*

In addition, `APIETAGProcessor` explicitly requires a function that (ideally) creates an ETag value from model instances.
If the `@api_etag` decorator is used without `etag_func` the framework will raise an `AssertionError`. 
Hence, the following snipped would not work:

    # BEGIN BAD CODE:
    class View(views.APIView):
        @api_etag() 
        def get(self, request, *args, **kwargs):
            return super(View, self).get(request, *args, **kwargs)
    # END BAD CODE

**Why's that?**
It does not make sense to compute a default ETag here, because the processor would lock us out from the API by always issuing a `304` 
response on conditional requests, even if the resource was modified meanwhile.
Therefore the `APIETAGProcessor` cannot be used without specifying an `etag_func` as keyword argument and there exists convenient 
[mixin classes](#apietagmixin).

You can use the decorator in regular `APIView`, and subclasses from the `rest_framework.generics` module, 
but ensure to include a `queryset` attribute or override `get_queryset()`:

    from rest_framework import generics
    from rest_framework.response import Response
    from rest_framework_extensions.utils import default_api_object_etag_func
    from my_app.models import Book
    
    class BookCustomDestroyView(generics.DestroyAPIView):  
        # include the queryset here to enable the object lookup 
        queryset = Book.objects.all()
    
        @api_etag(etag_func=default_api_object_etag_func)
        def delete(self, request, *args, **kwargs):
            obj = Book.objects.get(id=kwargs['pk'])
            # ... perform some custom operations here ...
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


The next difference to the `@etag` decorator is that it defines an explicit map of 
required headers for each HTTP request verb, using the following default values for unsafe methods:

    precondition_map = {'PUT': ['If-Match'],
                        'PATCH': ['If-Match'],
                        'DELETE': ['If-Match']}

You can specify a custom set of headers in the decorator by passing the `precondition_map` keyword argument.
For instance, this statement
  
    @api_etag(etag_func=default_api_object_etag_func, precondition_map={'PUT': ['X-mycorp-custom']})
    def put(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        # ... perform some custom operations here ...
        obj.save()
        return Response(status=status.HTTP_200_OK)

checks for the presence of a custom header `X-mycorp-custom` in the request and permits the request, if it is present, 
or returns a `428 PRECONDITION REQUIRED` response.

Similarly, to disable all checks for a particular method simply pass an empty dict:

    @api_etag(etag_func=default_api_object_etag_func, precondition_map={})
    def put(self, request, *args, **kwargs):
        obj = Book.objects.get(id=kwargs['pk'])
        # ... perform some custom operations here ...
        obj.save()
        return Response(status=status.HTTP_200_OK)

Please note that passing `None` in the `precondition_map` argument falls back to using the default map.

#### Usage ETag with caching

As you can see `@etag` and `@cache_response` decorators has similar key calculation approaches. 
They both can take key from simple callable function. And more than this - in many cases they share the same calculation logic. 
In the next example we use both decorators, which share one calculation function:

    from rest_framework_extensions.etag.decorators import etag
    from rest_framework_extensions.cache.decorators import cache_response
    from rest_framework_extensions.key_constructor import bits
    from rest_framework_extensions.key_constructor.constructors import (
        KeyConstructor
    )

    class CityGetKeyConstructor(KeyConstructor):
        format = bits.FormatKeyBit()
        language = bits.LanguageKeyBit()

    class CityView(views.APIView):
        key_constructor_func = CityGetKeyConstructor()

        @etag(key_constructor_func)
        @cache_response(key_func=key_constructor_func)
        def get(self, request, *args, **kwargs):
            cities = City.objects.all().values_list('name', flat=True)
            return Response(cities)

Note the decorators order. First goes `@etag` and then goes `@cache_response`. We want firstly perform conditional processing and after it response processing.

There is one more point for it. If conditional processing didn't fail then `key_constructor_func` would be called again in `@cache_response`.
But in most cases first calculation is enough. To accomplish this goal you could use `KeyConstructor` initial argument `memoize_for_request`:

    >>> key_constructor_func = CityGetKeyConstructor(memoize_for_request=True)
    >>> request1, request1 = 'request1', 'request2'
    >>> print key_constructor_func(request=request1)  # full calculation
    request1-key
    >>> print key_constructor_func(request=request1)  # data from cache
    request1-key
    >>> print key_constructor_func(request=request2)  # full calculation
    request2-key
    >>> print key_constructor_func(request=request2)  # data from cache
    request2-key

By default `memoize_for_request` is `False`, but you can change it in settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_KEY_CONSTRUCTOR_MEMOIZE_FOR_REQUEST': True
    }


It's important to note that this memoization is thread safe.

#### Saving time and bandwidth

When a server returns `ETag` header, you should store it along with the representation data on the client.
When making GET and HEAD requests for the same resource in the future, include the `If-None-Match` header
to make these requests "conditional". 

For example, retrieve all cities:

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8
    ETag: "some_etag_value"

    ['Moscow', 'London', 'Paris']

If you make same request with `If-None-Match` and there exists a cached value for this request,
then server will respond with `304` status code without body data.

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json
    If-None-Match: some_etag_value

    # Response
    HTTP/1.1 304 NOT MODIFIED
    Content-Type: application/json; charset=UTF-8
    Etag: "some_etag_value"

After this response you can use existing cities data on the client. 








#### Concurrency control

Concurrency control ensures the correct processing of data under concurrent operations by clients.
There are two ways to implement concurrency control:

* **Pessimistic concurrency control**. In this model, the client gets a lock, obtains
the current state of the resource, makes modifications, and then releases the lock.
During this process, the server prevents other clients from acquiring a lock on the same resource.
Relational databases operate in this manner.
* **Optimistic concurrency control**. In this model, the client first gets a token.
Instead of obtaining a lock, the client attempts a write operation with the token included in the request.
The operation succeeds if the token is still valid and fails otherwise.

HTTP, being a stateless application control, is designed for optimistic concurrency control.
According to [RFC 6585](https://tools.ietf.org/html/rfc6585), the server can optionally require 
a condition for a request. This library returns a `428` status, if no ETag is supplied, but would be mandatory 
for a request to succeed.

Update:

                                            PUT/PATCH
                                                +
                                    +-----------+------------+
                                    |         ETag           |
                                    |         supplied?      |
                                    ++-----------------+-----+
                                     |                 |
                                     Yes               No
                                     |                 |
               +---------------------++               ++-------------+
               |   Do preconditions   |               | Precondition |
               |   match?             |               | required?    |
               +---+-----------------++               ++------------++
                   |                 |                 |            |
                   Yes               No                No           Yes
                   |                 |                 |            |
        +----------+------+  +-------+----------+  +---+-----+      |
        |  Does resource  |  | 412 Precondition |  | 200 OK  |      |
        |  exist?         |  | failed           |  | Update  |      |
        ++---------------++  +------------------+  +---------+      |
         |               |                              +-----------+------+
         Yes             No                             | 428 Precondition |
         |               |                              | required         |
    +----+----+     +----+----+                         +------------------+
    | 200 OK  |     | 404 Not |
    | Update  |     | found   |
    +---------+     +---------+


Delete:

                                              DELETE
                                                +
                                    +-----------+------------+
                                    |         ETag           |
                                    |         supplied?      |
                                    ++-----------------+-----+
                                     |                 |
                                     Yes               No
                                     |                 |
               +---------------------++               ++-------------+
               |   Do preconditions   |               | Precondition |
               |   match?             |               | required?    |
               +---+-----------------++               ++------------++
                   |                 |                 |            |
                   Yes               No                No           Yes
                   |                 |                 |            |
        +----------+------+  +-------+----------+  +---+-----+      |
        |  Does resource  |  | 412 Precondition |  | 204 No  |      |
        |  exist?         |  | failed           |  | content |      |
        ++---------------++  +------------------+  +---------+      |
         |               |                              +-----------+------+
         Yes             No                             | 428 Precondition |
         |               |                              | required         |
    +----+----+     +----+----+                         +------------------+
    | 204 No  |     | 404 Not |
    | content |     | found   |
    +---------+     +---------+



**Example: transient key construction**

Here is an example implementation for all (C)RUD methods (except create, because it doesn't need concurrency control)
wrapped with the default `etag` decorator. We use our [previous implementation](#custom-key-bit) of the `UpdatedAtKeyBit` that looks up the cache 
for the last timestamp the particular object was updated on the server. This required us to add `post_save` and `post_delete` signals
to our models explicitly. See [below](#apietagmixin) for an example using `@api_etag` and mixins that computes the key from persistent data.

    from rest_framework.viewsets import ModelViewSet
    from rest_framework_extensions.key_constructor import bits
    from rest_framework_extensions.key_constructor.constructors import (
        KeyConstructor
    )

    from your_app.models import City
    # use our own implementation that detects an update timestamp in the cache 
    from your_app.key_bits import UpdatedAtKeyBit

    class CityListKeyConstructor(KeyConstructor):
        format = bits.FormatKeyBit()
        language = bits.LanguageKeyBit()
        pagination = bits.PaginationKeyBit()
        list_sql_query = bits.ListSqlQueryKeyBit()
        unique_view_id = bits.UniqueViewIdKeyBit()

    class CityDetailKeyConstructor(KeyConstructor):
        format = bits.FormatKeyBit()
        language = bits.LanguageKeyBit()
        retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
        unique_view_id = bits.UniqueViewIdKeyBit()
        updated_at = UpdatedAtKeyBit()

    class CityViewSet(ModelViewSet):
        list_key_func = CityListKeyConstructor(
            memoize_for_request=True
        )
        obj_key_func = CityDetailKeyConstructor(
            memoize_for_request=True
        )

        @etag(list_key_func)
        @cache_response(key_func=list_key_func)
        def list(self, request, *args, **kwargs):
            return super(CityViewSet, self).list(request, *args, **kwargs)

        @etag(obj_key_func)
        @cache_response(key_func=obj_key_func)
        def retrieve(self, request, *args, **kwargs):
            return super(CityViewSet, self).retrieve(request, *args, **kwargs)

        @etag(obj_key_func)
        def update(self, request, *args, **kwargs):
            return super(CityViewSet, self).update(request, *args, **kwargs)

        @etag(obj_key_func)
        def destroy(self, request, *args, **kwargs):
            return super(CityViewSet, self).destroy(request, *args, **kwargs)


#### ETag for unsafe methods

From previous section you could see that unsafe methods, such `update` (PUT, PATCH) or `destroy` (DELETE), have the same `@etag`
decorator wrapping manner as the safe methods.

But every unsafe method has one distinction from safe method - it changes the data
which could be used for Etag calculation. In our case it is `UpdatedAtKeyBit`. It means that we should calculate Etag:

* Before building response - for `If-Match` and `If-None-Match` conditions validation
* After building response (if necessary) - for clients

`@etag` decorator has special attribute `rebuild_after_method_evaluation`, which by default is `False`.

If you specify `rebuild_after_method_evaluation` as `True` then Etag will be rebuilt after method evaluation:

    class CityViewSet(ModelViewSet):
        ...
        @etag(obj_key_func, rebuild_after_method_evaluation=True)
        def update(self, request, *args, **kwargs):
            return super(CityViewSet, self).update(request, *args, **kwargs)

        @etag(obj_key_func)
        def destroy(self, request, *args, **kwargs):
            return super(CityViewSet, self).destroy(request, *args, **kwargs)

    # Request
    PUT /cities/1/ HTTP/1.1
    Accept: application/json

    {"name": "London"}

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8
    ETag: "4e63ef056f47270272b96523f51ad938b5ea141024b767880eac047d10a0b339"

    {
      id: 1,
      name: "London"
    }

As you can see we didn't specify `rebuild_after_method_evaluation` for `destroy` method. That is because there is no
sense to use returned ETag value on clients if object deletion already performed.

With `rebuild_after_method_evaluation` parameter Etag calculation for `PUT`/`PATCH` method would look like:

                 +--------------+
                 |    Request   |
                 +--------------+
                        |
           +--------------------------+
           |  Calculate Etag          |
           |  for condition matching  |
           +--------------------------+
                        |
              +--------------------+
              |  Do preconditions  |
              |  match?            |
              +--------------------+
                  |           |
                  Yes         No
                  |           |
      +--------------+  +--------------------+
      |  Update the  |  |  412 Precondition  |
      |  resource    |  |  failed            |
      +--------------+  +--------------------+
             |
    +--------------------+
    |  Calculate Etag    |
    |  again and add it  |
    |  to response       |
    +--------------------+
             |
       +------------+
       |  Return    |
       |  response  |
       +------------+

`If-None-Match` example for `DELETE` method:

    # Request
    DELETE /cities/1/ HTTP/1.1
    Accept: application/json
    If-None-Match: some_etag_value

    # Response
    HTTP/1.1 304 NOT MODIFIED
    Content-Type: application/json; charset=UTF-8
    Etag: "some_etag_value"


`If-Match` example for `DELETE` method:

    # Request
    DELETE /cities/1/ HTTP/1.1
    Accept: application/json
    If-Match: another_etag_value

    # Response
    HTTP/1.1 412 PRECONDITION FAILED
    Content-Type: application/json; charset=UTF-8
    Etag: "some_etag_value"


#### ETAGMixin

It is common to process etags for standard [viewset](http://www.django-rest-framework.org/api-guide/viewsets)
`retrieve`, `list`, `update` and `destroy` methods.
That is why `ETAGMixin` exists. Just mix it into viewset
implementation and those methods will use functions, defined in `REST_FRAMEWORK_EXTENSIONS` [settings](#settings):

* *"DEFAULT\_OBJECT\_ETAG\_FUNC"* for `retrieve`, `update` and `destroy` methods
* *"DEFAULT\_LIST\_ETAG\_FUNC"* for `list` method

By default those functions are using [DefaultKeyConstructor](#default-key-constructor) and extends it:

* With `RetrieveSqlQueryKeyBit` for *"DEFAULT\_OBJECT\_ETAG\_FUNC"*
* With `ListSqlQueryKeyBit` and `PaginationKeyBit` for *"DEFAULT\_LIST\_ETAG\_FUNC"*

You can change those settings for custom ETag generation:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_OBJECT_ETAG_FUNC':
          'rest_framework_extensions.utils.default_object_etag_func',
        'DEFAULT_LIST_ETAG_FUNC':
          'rest_framework_extensions.utils.default_list_etag_func',
    }

Mixin example usage:

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.etag.mixins import ETAGMixin

    class UserViewSet(ETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

You can change etag function by providing `object_etag_func` or
`list_etag_func` methods in view class:

    class UserViewSet(ETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

        def object_etag_func(self, **kwargs):
            return 'some key for object'

        def list_etag_func(self, **kwargs):
            return 'some key for list'

Of course you can use custom [key constructor](#key-constructor):

    from yourapp.key_constructors import (
        CustomObjectKeyConstructor,
        CustomListKeyConstructor,
    )

    class UserViewSet(ETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer
        object_etag_func = CustomObjectKeyConstructor()
        list_etag_func = CustomListKeyConstructor()

It is important to note that ETags for unsafe method `update` is processed with parameter
`rebuild_after_method_evaluation` equals `True`. You can read why from [this](#etag-for-unsafe-methods) section.

There are other mixins for more granular Etag calculation in `rest_framework_extensions.etag.mixins` module:

* **ReadOnlyETAGMixin** - only for `retrieve` and `list` methods
* **RetrieveETAGMixin** - only for `retrieve` method
* **ListETAGMixin** - only for `list` method
* **DestroyETAGMixin** - only for `destroy` method
* **UpdateETAGMixin** - only for `update` method


#### APIETagMixin

*New in DRF-extensions 0.3.2*

In analogy to `ETAGMixin` the `APIETAGMixin` exists. Just mix it into DRF viewsets or `APIViews` 
and those methods will use the ETag functions, defined in `REST_FRAMEWORK_EXTENSIONS` [settings](#settings):

* *"DEFAULT\_API\_OBJECT\_ETAG\_FUNC"* for `retrieve`, `update` and `destroy` methods
* *"DEFAULT\_API\_LIST\_ETAG\_FUNC"* for `list` method

By default those functions are using custom key constructors that create the key from **persisted model attributes**:

* `RetrieveModelKeyBit` (see [definition](#retrievemodelkeybit)) for *"DEFAULT\_API\_OBJECT\_ETAG\_FUNC"*
* `ListModelKeyBit` (see [definition](#listmodelkeybit)) for *"DEFAULT\_API\_LIST\_ETAG\_FUNC"*

You can change those settings globally for your custom ETag generation, or use the default values, which should cover 
the most common use cases:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_API_OBJECT_ETAG_FUNC': 
            'rest_framework_extensions.utils.default_api_object_etag_func',
        'DEFAULT_API_LIST_ETAG_FUNC': 
            'rest_framework_extensions.utils.default_api_list_etag_func',
    }

Mixin example usage:

    from myapps.serializers import UserSerializer
    from rest_framework_extensions.etag.mixins import APIETAGMixin

    class UserViewSet(APIETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

You can change etag function by providing `api_object_etag_func` or
`api_list_etag_func` methods in view class:

    class UserViewSet(APIETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

        def api_object_etag_func(self, **kwargs):
            return 'some key for object'

        def api_list_etag_func(self, **kwargs):
            return 'some key for list'

Of course you can use custom [key constructors](#key-constructor):

    from yourapp.key_constructors import (
        CustomObjectKeyConstructor,
        CustomListKeyConstructor,
    )

    class UserViewSet(APIETAGMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer
        api_object_etag_func = CustomObjectKeyConstructor()
        api_list_etag_func = CustomListKeyConstructor()

There are other mixins for more granular ETag calculation in `rest_framework_extensions.etag.mixins` module:

* **APIReadOnlyETAGMixin** - only for `retrieve` and `list` methods
* **APIRetrieveETAGMixin** - only for `retrieve` method
* **APIListETAGMixin** - only for `list` method
* **APIDestroyETAGMixin** - only for `destroy` method
* **APIUpdateETAGMixin** - only for `update` method

By default, all mixins require the conditional requests, i.e. they use the default `precondition_map` from the 
`APIETAGProcessor` class.


#### Gzipped ETags

If you use [GZipMiddleware](https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.gzip)
and your client accepts Gzipped response, then you should return different ETags for compressed and not compressed responses.
That's what `GZipMiddleware` does by default while processing response -
it adds `;gzip` postfix to ETag response header if client requests compressed response.
Lets see it in example. First request without compression:

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8
    ETag: "e7b50490dc"

    ['Moscow', 'London', 'Paris']

Second request with compression:

    # Request
    GET /cities/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip

    # Response
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 675
    Content-Encoding: gzip
    ETag: "e7b50490dc;gzip"

    wS?n?0?_%o?cc?Ҫ?Eʒ?Cժʻ?a\1?a?^T*7q<>[Nvh?[?^9?x:/Ms?79?Fd/???ۦjES?ڽ?&??c%^?C[K۲%N?w{?졭2?m?}?Q&Egz??

As you can see there is `;gzip` postfix in ETag response header.
That's ok but there is one caveat - drf-extension doesn't know how you post-processed calculated ETag value.
And your clients could have next problem with conditional request:

* Client sends request to retrieve compressed data about cities to `/cities/`
* DRF-extensions decorator calculates ETag header for response equals, for example, `123`
* `GZipMiddleware` adds `;gzip` postfix to ETag header response, and now it equals `123;gzip`
* Client retrieves response with ETag equals `123;gzip`
* Client again makes request to retrieve compressed data about cities,
but now it's conditional request with `If-None-Match` header equals `123;gzip`
* DRF-extensions decorator calculates ETag value for processing conditional request.
But it doesn't know, that `GZipMiddleware` added `;gzip` postfix for previous response.
DRF-extensions decorator calculates ETag equals `123`, compares it with `123;gzip` and returns
response with status code 200, because `123` != `123;gzip`

You can solve this problem by stripping `;gzip` postfix on client side.

But there are so many libraries that just magically uses ETag response header without allowing to
pre-process conditional requests (for example, browser). If that's you case then you could add custom middleware which removes `;gzip`
postfix from header:

    # yourapp/middleware.py

    class RemoveEtagGzipPostfix(object):
        def process_response(self, request, response):
            if response.has_header('ETag') and response['ETag'][-6:] == ';gzip"':
                response['ETag'] = response['ETag'][:-6] + '"'
            return response

Don't forget to add this middleware in your settings before `GZipMiddleware`:

    # settings.py
    MIDDLEWARE_CLASSES = (
        ...
        'yourapp.RemoveEtagGzipPostfix',
        'django.middleware.gzip.GZipMiddleware',
        'django.middleware.common.CommonMiddleware',
        ...
    )




### Bulk operations

*New in DRF-extensions 0.2.4*

Bulk operations allows you to perform operations over set of objects with one request. There is third-party package
[django-rest-framework-bulk](django-rest-framework-bulk) with support for all CRUD methods, but it iterates over every
instance in bulk operation, serializes it and only after that executes operation.

It plays nice with `create` or `update`
operations, but becomes unacceptable with `partial update` and `delete` methods over the `QuerySet`. Such kind of
`QuerySet` could contain thousands of objects and should be performed as database query over the set at once.

Please note - DRF-extensions bulk operations applies over `QuerySet`, not over instances. It means that:

* No serializer's `save` or `delete` methods would be called
* No viewset's `pre_save`, `post_save`, `pre_delete` and `post_delete` would be called
* No model signals would be called

#### Safety

Bulk operations are very dangerous in case of making stupid mistakes. For example you wanted to delete user instance
with `DELETE` request from your client application.

    # Request
    DELETE /users/1/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 204 NO CONTENT
    Content-Type: application/json; charset=UTF-8

That was example of successful deletion. But there is the common situation when client could not get instance id and sends
request to endpoint without it:

    # Request
    DELETE /users/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 204 NO CONTENT
    Content-Type: application/json; charset=UTF-8

If you used [bulk destroy mixin](#bulk-destroy) for `/users/` endpoint, then all your user objects would be deleted.

To protect from such confusions DRF-extensions asks you to send `X-BULK-OPERATION` header
for every bulk operation request. With this protection previous example would not delete any user instances:

    # Request
    DELETE /users/ HTTP/1.1
    Accept: application/json

    # Response
    HTTP/1.1 400 BAD REQUEST
    Content-Type: application/json; charset=UTF-8

    {
      "detail": "Header 'X-BULK-OPERATION' should be provided for bulk operation."
    }


With `X-BULK-OPERATION` header it works as expected - deletes all user instances:

    # Request
    DELETE /users/ HTTP/1.1
    Accept: application/json
    X-BULK-OPERATION: true

    # Response
    HTTP/1.1 204 NO CONTENT
    Content-Type: application/json; charset=UTF-8

You can change bulk operation header name in settings:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_BULK_OPERATION_HEADER_NAME': 'X-CUSTOM-BULK-OPERATION'
    }

To turn off protection you can set `DEFAULT_BULK_OPERATION_HEADER_NAME` as `None`.

#### Bulk destroy

This mixin allows you to delete many instances with one `DELETE` request.

    from rest_framework_extensions.bulk_operations.mixins import ListDestroyModelMixin

    class UserViewSet(ListDestroyModelMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

Bulk destroy example - delete all users which emails ends with `gmail.com`:

    # Request
    DELETE /users/?email__endswith=gmail.com HTTP/1.1
    Accept: application/json
    X-BULK-OPERATION: true

    # Response
    HTTP/1.1 204 NO CONTENT
    Content-Type: application/json; charset=UTF-8

#### Bulk update

This mixin allows you to update many instances with one `PATCH` request. Note, that this mixin works only with partial update.

    from rest_framework_extensions.mixins import ListUpdateModelMixin

    class UserViewSet(ListUpdateModelMixin, viewsets.ModelViewSet):
        serializer_class = UserSerializer

Bulk partial update example - set `email_provider` of every user as `google`, if it's email ends with `gmail.com`:

    # Request
    PATCH /users/?email__endswith=gmail.com HTTP/1.1
    Accept: application/json
    X-BULK-OPERATION: true

    {"email_provider": "google"}

    # Response
    HTTP/1.1 204 NO CONTENT
    Content-Type: application/json; charset=UTF-8

### Settings

DRF-extensions follows Django Rest Framework approach in settings implementation.

[In Django Rest Framework](http://www.django-rest-framework.org/api-guide/settings) you specify custom settings by changing `REST_FRAMEWORK` variable in settings file:

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.YAMLRenderer',
        ),
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.YAMLParser',
        )
    }

In DRF-extensions there is a magic variable too called `REST_FRAMEWORK_EXTENSIONS`:

    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
    }

#### Accessing settings

If you need to access the values of DRF-extensions API settings in your project, you should use the `extensions_api_settings` object. For example:

    from rest_framework_extensions.settings import extensions_api_settings

    print extensions_api_settings.DEFAULT_CACHE_RESPONSE_TIMEOUT

### Release notes

You can read about versioning, deprecation policy and upgrading from
[Django REST framework documentation](http://django-rest-framework.org/topics/release-notes).

#### 0.3.2

*Jan 4, 2017*

* Added `rest_framework_extensions.exceptions.PreconditionRequiredException` as subclass of `rest_framework.exceptions.APIException`
* Added `@api_etag` decorator function and `APIETAGProcessor` that uses *semantic* ETags per API resource, decoupled from views, such that it can be used in optimistic concurrency control 
* Added new default key bits `RetrieveModelKeyBit` and `ListModelKeyBit` for computing the semantic fingerprint of a django model instance
* Added `APIETAGMixin` to be used in DRF viewsets and views
* Added new settings for default implementation of the API ETag functions: `DEFAULT_API_OBJECT_ETAG_FUNC`, `DEFAULT_API_LIST_ETAG_FUNC`
* Added test application for functional tests and demo as `tests_app/tests/functional/concurrency/conditional_request`
* Added unit tests for the `@api_etag` decorator
* DRF 3.5.x, Django pre-1.10 compatibility of the key bit construction
* (Test-)Code cleanup

#### 0.3.1

*Sep 29, 2016*

* Fix `schema_urls` `ExtendedDefaultRouter` compatibility issue introduced by DRF 3.4.0
* Removed deprecated @action() and @link() decorators
* DRF 3.4.x compatibility
* Django 1.9 and 1.10 compatibility

#### 0.2.8

*Sep 21, 2015*

* Fixed `ListSqlQueryKeyBit` and `RetrieveSqlQueryKeyBit` [problems](https://github.com/chibisov/drf-extensions/issues/28) with `EmptyResultSet` exception ([pull](https://github.com/chibisov/drf-extensions/pull/75/)).
* All items are now by default in [ArgsKeyBit](#argskeybit), [KwargsKeyBit](#kwargskeybit) and [QueryParamsKeyBit](#queryparamskeybit)
* Respect parent lookup regex value for [Nested routes](#nested-routes) ([issue](https://github.com/chibisov/drf-extensions/pull/87)).

#### 0.2.7

*Feb 2, 2015*

* [DRF 3.x compatibility](https://github.com/chibisov/drf-extensions/issues/39)
* [DetailSerializerMixin](#detailserializermixin) is now [compatible with DRF 3.0](https://github.com/chibisov/drf-extensions/issues/46)
* Added [ArgsKeyBit](#argskeybit)
* Added [KwargsKeyBit](#kwargskeybit)
* Fixed [PartialUpdateSerializerMixin](#partialupdateserializermixin) [compatibility issue with DRF 3.x](https://github.com/chibisov/drf-extensions/issues/66)
* Added [cache_errors](#caching-errors) attribute for switching caching for error responses
* Added ability to specify usage of all items for [RequestMetaKeyBit](#requestmetakeybit), [HeadersKeyBit](#headerskeybit)
and [QueryParamsKeyBit](#queryparamskeybit) providing `params='*'`
* [Collection level controllers](#collection-level-controllers) is in pending deprecation
* [Controller endpoint name](#controller-endpoint-name) is in pending deprecation

#### 0.2.6

*Sep 9, 2014*

* Usage of [django.core.cache.caches](https://docs.djangoproject.com/en/dev/topics/cache/#django.core.cache.caches) for
django >= 1.7
* [Documented ETag usage with GZipMiddleware](#gzipped-etags)
* Fixed `ListSqlQueryKeyBit` and `RetrieveSqlQueryKeyBit` [problems](https://github.com/chibisov/drf-extensions/issues/28)
with `EmptyResultSet`.
* Fixed [cache response](#cache-response) compatibility [issue](https://github.com/chibisov/drf-extensions/issues/32)
with DRF 2.4.x

#### 0.2.5

*July 9, 2014*

* Fixed [setuptools confusion with pyc files](https://github.com/chibisov/drf-extensions/issues/20)

#### 0.2.4

*July 7, 2014*

* Added tests for [Django REST Framework 2.3.14](http://www.django-rest-framework.org/topics/release-notes#2314)
* Added [Bulk operations](#bulk-operations)
* Fixed [extended routers](#routers) compatibility issue with [default controller decorators](http://www.django-rest-framework.org/api-guide/viewsets#marking-extra-methods-for-routing)
* Documented [pluggable router mixins](#pluggable-router-mixins)
* Added [nested routes](#nested-routes)

#### 0.2.3

*Apr. 25, 2014*

* Added [PartialUpdateSerializerMixin](#partialupdateserializermixin)
* Added [Key constructor params](#key-constructor-params)
* Documented dynamically [constructor's bits list](#constructor-s-bits-list) altering
* Added ability to [use a specific cache](#usage-of-the-specific-cache) for `@cache_response` decorator

#### 0.2.2

*Mar. 23, 2014*

* Added [PaginateByMaxMixin](#paginatebymaxmixin)
* Added [ExtenedDjangoObjectPermissions](#object-permissions)
* Added tests for django 1.7

#### 0.2.1

*Feb. 1, 2014*

* Rewritten tests to nose and tox
* New tests directory structure
* Rewritten HTTP documentation requests examples into more raw manner
* Added trailing_slash on extended routers for Django Rest Framework versions`>=2.3.6` (which supports this feature)
* Added [caching](#caching)
* Added [key constructor](#key-constructor)
* Added [conditional requests](#conditional-requests) with Etag calculation
* Added [Cache/ETAG mixins](#cache-etag-mixins)
* Added [CacheResponseMixin](#cacheresponsemixin)
* Added [ETAGMixin](#etagmixin)
* Documented [ResourceUriField](#resourceurifield)
* Documented [settings](#settings) customization

#### 0.2

*Nov. 5, 2013*

* Moved docs from readme to github pages
* Docs generation with [Backdoc](https://github.com/chibisov/backdoc)
