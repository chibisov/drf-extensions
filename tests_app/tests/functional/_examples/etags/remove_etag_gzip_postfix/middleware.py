try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class RemoveEtagGzipPostfix(MiddlewareMixin):
    def process_response(self, request, response):
        if response.has_header('ETag') and response['ETag'][-6:] == ';gzip"':
            response['ETag'] = response['ETag'][:-6] + '"'
        return response
