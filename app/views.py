import asyncio
import time

from django import http
from django.conf import settings
from django.core import signals


def sync_view(request):
    if settings.DELAY:
        time.sleep(settings.DELAY)
    return http.HttpResponse(content=request.body)


async def async_view(request):
    if settings.DELAY:
        await asyncio.sleep(settings.DELAY)
    return http.HttpResponse(content=request.body)


class Receiver:
    value = 0

    def __call__(self, **kwargs):
        self.value += 1


class AsyncReceiver:
    _is_coroutine = asyncio.coroutines._is_coroutine
    value = 0

    async def __call__(self, **kwargs):
        self.value += 1


receivers = []

for i in range(settings.SYNC_RECEIVERS_COUNT):
    r = Receiver()
    receivers.append(r)
    signals.request_started.connect(r)
    signals.request_finished.connect(r)


for i in range(settings.ASYNC_RECEIVERS_COUNT * 2):
    r = AsyncReceiver()
    receivers.append(r)
    signals.request_started.connect(r)
    # signals.request_finished.connect(r)
