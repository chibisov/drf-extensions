# -*- coding: utf-8 -*-


class RemoveEtagGzipPostfix(object):
    def process_response(self, request, response):
        if response.has_header('ETag') and response['ETag'][-6:] == ';gzip"':
            response['ETag'] = response['ETag'][:-6] + '"'
        return response