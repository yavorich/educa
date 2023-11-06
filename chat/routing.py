from django.urls import re_path
from . import consumers

# К URL-адресам веб-сокетов рекомендуется добавлять префикс /ws/, 
# чтобы отличать их от URL-адресов, используемых для стандартных синхронных HTTPзапросов.

websocket_urlpatterns = [
    re_path(r'ws/chat/room/(?P<course_id>\d+)/$',
            consumers.ChatConsumer.as_asgi()),
]