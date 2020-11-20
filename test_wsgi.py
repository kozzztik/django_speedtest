import os
import timeit

import django
from django.core.wsgi import get_wsgi_application


REPEAT_COUNT = 1

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')


class Executor:
    def __init__(self):
        self.app = get_wsgi_application()

    def _start_response(self, status, response_headers):
        pass

    @staticmethod
    def read(size):
        """ Interface of request stream """
        return b'ping'[:size]

    def __call__(self):
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/sync/',
            'wsgi.input': self,
            'CONTENT_LENGTH': 4,
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': 0,
        }
        response = self.app(environ, self._start_response)
        if response.status_code != 200 or response.content != b'ping':
            raise Exception('Wrong response')


executor = Executor()


print(django.VERSION)
print(timeit.timeit(executor, number=REPEAT_COUNT))
