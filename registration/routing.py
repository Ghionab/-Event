"""
WebSocket routing for registration app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/calendar/$', consumers.CalendarConsumer.as_asgi()),
    re_path(r'ws/event/(?P<event_id>\d+)/$', consumers.EventUpdateConsumer.as_asgi()),
]
