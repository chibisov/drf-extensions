from django.views import View
from django.http import HttpResponse


class MyView(View):
    def get(self, request):
        """
        GZipMiddleware will NOT compress content if any of the following are true:
            * The content body is less than 200 bytes long.
            * The response has already set the Content-Encoding header.
            * The request (the browser) hasn’t sent an Accept-Encoding header containing gzip.
        """
        response = HttpResponse('r' * 300)
        response['ETag'] = '"etag_value"'
        return response
