import asyncio
import os
import timeit

import asgiref
import django
from django.core.asgi import get_asgi_application
try:
    from django_websockets2.asgi_handler import \
        get_asgi_application as get_fast_asgi_application
except ImportError:
    get_fast_asgi_application = None


REPEAT_COUNT = 10000
FAST_ASGI = False
ASYNC_VIEW = True

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')


class Context:
    status_code = None
    content = None

    async def send(self, data):
        if data['type'] == 'http.response.start':
            self.status_code = data['status']
        elif data['type'] == 'http.response.body':
            self.content = self.content or b'' + data['body']

    @staticmethod
    async def receive():
        return {
            'type': '',
            'body': b'ping'
        }


class Executor:
    def __init__(self):
        if FAST_ASGI:
            self.app = get_fast_asgi_application()
        else:
            self.app = get_asgi_application()

    def __call__(self):
        scope = {
            'type': 'http',
            'path': '/async/' if ASYNC_VIEW else '/sync/',
            'method': 'GET',
        }
        response = Context()
        asyncio.run(self.app(scope, response.receive, response.send))
        if response.status_code != 200 or response.content != b'ping':
            raise Exception('Wrong response')


executor = Executor()

print(django.VERSION)
print(asgiref.__file__)
print(timeit.timeit(executor, number=REPEAT_COUNT))
