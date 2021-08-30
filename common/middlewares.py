from django.db import connection
from rest_framework.exceptions import ValidationError
from django.conf import settings
import jwt
import redis
from myapp.models import User
from myapp.token import *
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache import cache

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


class QueryCountDebugMiddleware(object):
    """Debug query count - use for DEBUG only."""
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        total_time = 0

        for query in connection.queries:
            query_time = query.get('time')
            print(str(query))

            if query_time is None:
                query_time = query.get('duration', 0) / 1000
            total_time += float(query_time)

        print('%s queries run, total %s seconds' % (len(connection.queries), total_time))
        return response


class AddTokenHeader(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            access_token = request.COOKIES.get('access_token')
            get_refresh_token = cache.get('refresh_token')
            if access_token and get_refresh_token:
                try:
                    jwt.decode(access_token, key=settings.SECRET_KEY, algorithms=["HS256"])
                except jwt.exceptions.ExpiredSignatureError:
                    payload = jwt.decode(get_refresh_token, key=settings.REFRESH_KEY, algorithms=["HS256"])
                    user = User.objects.get(id=payload.get('id'))
                    access_token = generate_access_token(user)
                    request.COOKIES['access_token'] = access_token
                except Exception as e:
                    raise ValidationError(e)
                request.META['HTTP_AUTHORIZATION'] = "Token" + ' ' + access_token
            response = self.get_response(request)
            return response
        except Exception as e:
            raise ValidationError(e)
