import logging
from functools import wraps

from django.utils.decorators import available_attrs
from rest_framework import status

from rest_framework_extensions.exceptions import PreconditionRequiredException
from rest_framework_extensions.utils import prepare_header_name

logger = logging.getLogger('django.request')


class PreconditionRequiredProcessor(object):
    """
    This class performs checks for required pre-conditional headers for view methods.

    According to RFC 6585, conditional headers may be enforced for certain services that support conditional
    requests. For optimistic locking, the server should respond status code 428 including a description on how
    to resubmit the request successfully, see https://tools.ietf.org/html/rfc6585#section-3.
    """

    # require a pre-conditional header (e.g. 'If-Match') for unsafe HTTP methods (RFC 6585)
    # override this defaults, if required
    precondition_map = {'PUT': ['If-Match'],
                        'PATCH': ['If-Match'],
                        'DELETE': ['If-Match']}

    def __init__(self, precondition_map=None):
        if precondition_map is not None:
            self.precondition_map = precondition_map
        assert isinstance(self.precondition_map, dict), ('`precondition_map` must be a dict, where '
                                                         'the key is the HTTP verb, and the value is a list of '
                                                         'HTTP headers that must all be present for that request.')

    def __call__(self, func):
        this = self

        @wraps(func, assigned=available_attrs(func))
        def inner(self, request, *args, **kwargs):
            # compute the preconditions
            errors = this.evaluate_preconditions(request=request,
                                                 args=args,
                                                 kwargs=kwargs)

            if len(errors) != 0:
                # raises 428 exception that will be caught by DRF
                raise this.prepare_exception(request, errors)
            else:
                # call the wrapped function, may be a view,
                # or another view method decorator such as @etag
                return func(self, request, *args, **kwargs)

        return inner

    def evaluate_preconditions(self, request, *args, **kwargs):
        """Evaluate whether the precondition for the request is met."""
        errors = {}

        if request.method.upper() in self.precondition_map.keys():
            required_headers = self.precondition_map.get(request.method.upper(), [])
            # check the required headers
            for header in list(required_headers):
                if not request.META.get(prepare_header_name(header)):
                    # collect errors
                    errors[header] = {'detail': 'This header is required.'}
        return errors

    def prepare_exception(self, request, errors):
        logger.warning('Precondition required: %s', request.path,
                       extra={
                           'status_code': status.HTTP_428_PRECONDITION_REQUIRED,
                           'request': request
                       }
                       )

        # raise an RFC 6585 compliant exception
        exception = PreconditionRequiredException(detail='Precondition required. This "%s" request '
                                                         'is required to be conditional. '
                                                         'Try again by providing all following HTTP headers: '
                                                         '"%s".' % (request.method,
                                                                    ", ".join(errors.keys()))
                                                  )
        return exception


# alias for decorator-style calls
precondition_required = PreconditionRequiredProcessor
