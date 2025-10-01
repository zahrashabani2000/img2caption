from django.urls import path
from .views import ui, chat

urlpatterns = [
    path('ui', ui, name='ui'),
    path('ui/', ui, name='ui-slash'),
    path('chat', chat, name='chat'),
    path('chat/', chat, name='chat-slash'),
]


