import asyncio
import functools
import logging


class ServerProtocol(asyncio.StreamReaderProtocol):
    def __init__(self, app, loop=None):
        self.app = app
        reader = asyncio.StreamReader(loop=loop)
        super(ServerProtocol, self).__init__(
            reader, loop=loop, client_connected_cb=self.handle_client)

    async def handle_client(self, stream_reader, stream_writer):
        while True:
            data = await stream_reader.readline()
            if not data:
                break
            try:
                status_code, body = await self.app(data.strip())
            except Exception as e:
                logging.exception(e)
                status_code = 500
                body = str(e).encode('utf8')
            stream_writer.write(f'{status_code} '.encode('utf8') + body + b'\n')
            await stream_writer.drain()
        stream_writer.close()


class ClientProtocol(asyncio.StreamReaderProtocol):
    def __init__(self, loop=None):
        self.stream_reader = asyncio.StreamReader(loop=loop)
        super().__init__(self.stream_reader, loop=loop)

    def connection_made(self, transport):
        super().connection_made(transport)
        self._stream_writer = asyncio.StreamWriter(
            transport, self, self.stream_reader, self._loop)

    async def do_request(self, body):
        self._stream_writer.write(body + b'\n')
        response = await self.stream_reader.readline()
        status_code, content = response.split(b' ', 1)
        if status_code != b'200' or content != body + b'\n':
            raise Exception(f'Wrong response: {response}')


class BaseApp:
    def __init__(self, view_url, handler):
        self.view_url = view_url
        self.handler = handler


class WSGIContext:
    def __init__(self, request):
        self.request = request

    def read(self, size):
        """ Interface of request stream """
        return self.request[:size]


class WSGIApp(BaseApp):
    def _start_response(self, status, response_headers):
        pass

    def get_environ(self, body):
        return {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': self.view_url,
            'wsgi.input': WSGIContext(body),
            'CONTENT_LENGTH': len(body),
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': 0,
        }

    async def __call__(self, body):
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(
                self.handler, self.get_environ(body), self._start_response))
        response.close()
        return response.status_code, response.content


class WSGISingleThreadApp(WSGIApp):
    async def __call__(self, body):
        response = self.handler(self.get_environ(body), self._start_response)
        response.close()
        return response.status_code, response.content


class ASGIContext:
    status_code = None
    content = None

    def __init__(self, request):
        self.request = request

    async def send(self, data):
        if data['type'] == 'http.response.start':
            self.status_code = data['status']
        elif data['type'] == 'http.response.body':
            self.content = self.content or b'' + data['body']

    async def receive(self):
        return {
            'type': '',
            'body': self.request
        }


class ASGIApp(BaseApp):
    async def __call__(self, body):
        scope = {
            'type': 'http',
            'path': self.view_url,
            'method': 'GET',
        }
        response = ASGIContext(body)
        await self.handler(scope, response.receive, response.send)
        return response.status_code, response.content
