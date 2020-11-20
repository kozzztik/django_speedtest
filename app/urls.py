from django.conf import urls
from app import views


urlpatterns = [
    urls.re_path(r'^sync/$', views.sync_view),
    urls.re_path(r'^async/$', views.async_view),
]
