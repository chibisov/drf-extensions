from rest_framework_extensions.decorators import precondition_required
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.etag.mixins import BaseETAGMixin, APIListETAGMixin, APIRetrieveETAGMixin


class OCCAPIUpdateETAGMixin(BaseETAGMixin):
    """
    A mixin that enforces a conditional request for an update (PUT/PATCH) operation.
    The resource version must be provided as `ETag` using the `If-Match` HTTP header.
    """
    @precondition_required(precondition_map={'PUT': ['If-Match'], 'PATCH': ['If-Match']})
    @etag(etag_func='api_object_etag_func', rebuild_after_method_evaluation=True)
    def update(self, request, *args, **kwargs):
        return super(OCCAPIUpdateETAGMixin, self).update(request, *args, **kwargs)


class OCCAPIDestroyETAGMixin(BaseETAGMixin):
    """
    A mixin that enforces a conditional request for a delete (DELETE) operation.
    The resource version must be provided as `ETag` using the `If-Match` HTTP header.
    """
    @precondition_required(precondition_map={'DELETE': ['If-Match']})
    @etag(etag_func='api_object_etag_func')
    def destroy(self, request, *args, **kwargs):
        return super(OCCAPIDestroyETAGMixin, self).destroy(request, *args, **kwargs)


class OCCAPIETAGMixin(APIListETAGMixin,
                      APIRetrieveETAGMixin,
                      OCCAPIUpdateETAGMixin,
                      OCCAPIDestroyETAGMixin):

    """
    A mixin that *enforces* optimistic concurrency control (OCC) using `ETag`s for DRF API views and viewsets.

    The API resource version identifiers are retrieved as HTTP `ETag` headers. PUT, PATCH, and DELETE HTTP
    request methods are required to be conditional, i.e. the client must provide a valid `ETag` in the HTTP
    `If-Match` header. Creating API resources using POST requests as well as listing and retrieval
    operations using GET requests do not require conditions. However, if provided on a GET method, the
    `If-None-Match` header will be used to create a 304 response in order to tell the client that the resource
    was not modified.
    """
    pass
