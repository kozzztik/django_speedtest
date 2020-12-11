import asyncio
import time

from django import http
from django.conf import settings


def sync_view(request):
    if settings.DELAY:
        time.sleep(settings.DELAY)
    return http.HttpResponse(content=request.body)


async def async_view(request):
    if settings.DELAY:
        await asyncio.sleep(settings.DELAY)
    return http.HttpResponse(content=request.body)

