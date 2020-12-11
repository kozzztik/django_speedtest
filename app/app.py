import asyncio

from django import apps
from django.conf import settings
from django.core import signals


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


class App(apps.AppConfig):
    name = 'app'

    def ready(self):
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
