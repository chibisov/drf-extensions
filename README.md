# Django REST Framework extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework)

[![Build Status](https://travis-ci.org/chibisov/drf-extensions.png?branch=master)](https://travis-ci.org/chibisov/drf-extensions)

# Installation:

    pip install drf-extensions

# Extensions

Extended @action, @link decorators and ExtendedDefaultRouter example.

    class DistributionViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = DistributionNews.objects.all()
        serializer_class = DistributionSerializer

        # curl -X POST /v1/distributions/1/unsubscribe/
        @action(permission_classes=[permissions.IsAuthenticated])
        def unsubscribe(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/unsubscribe/
        @action(endpoint='unsubscribe',
                is_for_list=True,
                permission_classes=[permissions.IsAuthenticated])
        def unsubscribe_from_all(self, request, *args, **kwargs):
            pass

        # curl /v1/distributions/1/unsubscribe-by-code/?code=xxxx
        @link(endpoint='unsubscribe-by-code')
        def unsubscribe_by_code(self, request, *args, **kwargs):
            pass

        # curl /v1/distributions/unsubscribe-by-code/?code=xxxx
        @link(endpoint='unsubscribe-by-code', is_for_list=True)
        def unsubscribe_by_code_from_all(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/1/subscribe/
        @action(permission_classes=[permissions.IsAuthenticated])
        def subscribe(self, request, *args, **kwargs):
            pass

        # curl -X POST /v1/distributions/subscribe/
        @action(endpoint='subscribe',
                is_for_list=True,
                permission_classes=[permissions.IsAuthenticated])
        def subscribe_to_all(self, request, *args, **kwargs):
            pass


    from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
    router = DefaultRouter()
    router.register(r'distributions', DistributionViewSet, base_name='distribution')
    urlpatterns = router.urls

DetailSerializerMixin lets add custom serializer for detail view:

    class SurveySerializer(serializers.ModelSerializer):
        class Meta:
            model = Survey
            fields = (
                'id',
                'name',
            )


    class SurveySerializerDetail(serializers.ModelSerializer):
        class Meta:
            model = Survey
            fields = (
                'id',
                'name',
                'form',
            )


    from rest_framework_extensions.mixins import DetailSerializerMixin

    class SurveyViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
        serializer_class = SurveySerializer
        serializer_detail_class = SurveySerializerDetail
        queryset = Survey.objects.all()

How to run tests locally:

    $ python setup.py test