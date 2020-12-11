import asyncio
import collections
import logging
import os
import time
import multiprocessing

import asgiref
import django
from django.core.wsgi import get_wsgi_application
from django.core.asgi import get_asgi_application

from utils import protocol
from app import app as test_app

try:
    from django_websockets2.asgi_handler import \
        get_asgi_application as get_fast_asgi_application
except ImportError:
    get_fast_asgi_application = None


HOST = '127.0.0.1'
PORT = 8000
PARALLEL = 1
REPEAT_COUNT = 10000
SYNC_VIEW = False
ASGI = False
# if asgi, then
FAST_ASGI = False
# if not asgi
FAST_WSGI = True

request_count = 0
request_time = 0
start_time = 0

ns = 1000000000
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')


def server_func(server_started, server_stopped):
    if ASGI:
        app_class = protocol.ASGIApp
        if FAST_ASGI:
            handler = get_fast_asgi_application()
        else:
            handler = get_asgi_application()
    else:
        handler = get_wsgi_application()
        if FAST_WSGI:
            app_class = protocol.WSGISingleThreadApp
        else:
            app_class = protocol.WSGIApp
    app = app_class('/sync/' if SYNC_VIEW else '/async/', handler)
    loop = asyncio.get_event_loop()
    create_server = loop.create_server(
        host=HOST, port=PORT,
        protocol_factory=lambda: protocol.ServerProtocol(app, loop=loop))
    server = loop.run_until_complete(create_server)

    def stop_signal(server):
        server_stopped.wait()
        server.close()
    loop.run_in_executor(None, stop_signal, server)
    print(f'Server started on {HOST}:{PORT}...')
    server_started.set()
    try:
        loop.run_until_complete(server.serve_forever())
    except asyncio.CancelledError:
        pass
    finally:
        value = 0
        for r in test_app.receivers:
            value += r.value
        print(f'Calls count: {value}')
        counter = collections.Counter([r.value for r in test_app.receivers])
        print(counter)


async def client_task():
    global request_count
    global request_time
    loop = asyncio.get_event_loop()
    transport, client = await loop.create_connection(
        protocol_factory=protocol.ClientProtocol, host=HOST, port=PORT)
    try:
        while request_count < REPEAT_COUNT:
            request_count += 1
            request_start_time = time.perf_counter_ns()
            try:
                await client.do_request(
                    f'ping {request_count}'.encode('utf-8'))
            except Exception as e:
                logging.exception(e)
                raise
            finally:
                request_time += time.perf_counter_ns() - request_start_time
    finally:
        transport.close()


def print_status():
    total_time = time.perf_counter_ns() - start_time
    print(f'Requests {request_count}, time: {request_time / ns}s '
          f'total time: {total_time / ns}s')


async def print_task():
    while True:
        await asyncio.sleep(15)
        if request_count >= REPEAT_COUNT:
            break
        print_status()


def main():
    if ASGI:
        if FAST_ASGI:
            implementation = 'FAST_ASGI'
        else:
            implementation = 'DJANGO_ASGI'
    else:
        if FAST_WSGI:
            implementation = 'WSGI (single threaded)'
        else:
            implementation = 'WSGI (multi threaded)'
    print(f'====== {implementation} PARALLEL: {PARALLEL} COUNT: {REPEAT_COUNT}'
          f' SYNC_VIEW: {SYNC_VIEW} ========')
    print(f'Django version: {".".join(map(str, django.VERSION))}')
    print(f'asgiref: {asgiref.__file__}')
    print('Creating server...')
    server_started = multiprocessing.Event()
    server_stopped = multiprocessing.Event()
    process = multiprocessing.Process(
        target=server_func, args=(server_started, server_stopped))
    process.start()
    server_started.wait()
    print('Starting client')
    loop = asyncio.get_event_loop()
    loop.create_task(print_task())
    tasks = []
    for i in range(PARALLEL):
        tasks.append(loop.create_task(client_task()))
    global start_time
    start_time = time.perf_counter_ns()
    loop.run_until_complete(asyncio.wait(tasks))
    print('====== Requests finished. ======')
    print_status()
    total_time = time.perf_counter_ns() - start_time
    server_stopped.set()
    process.join()
    for task in tasks:
        task.result()  # may raise
    print('Timing:')
    print(total_time / ns)


if __name__ == '__main__':
    main()
