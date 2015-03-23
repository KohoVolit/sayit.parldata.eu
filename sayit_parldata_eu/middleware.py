import time

from django.conf import settings
from django.utils.http import http_date
from django.utils.cache import patch_cache_control

class PatchCacheHeadersMiddleware(object):
    """
    Patch caching-related response headers to instruct the client that
    it should cache the response only for a short time of
    `CACHE_MIDDLEWARE_SECONDS`.

    Rendered responses are cached on the server forever (until
    explicitly requested refresh) but in client's browser, with help of
    this middleware, only for a short time . Thus if a page is
    re-rendered and refresed in server-side cache it updates on the
    client soon.
    """
    def process_response(self, request, response):
        client_cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        response['Expires'] = http_date(time.time() + client_cache_timeout)
        patch_cache_control(response, max_age=client_cache_timeout)
        return response
