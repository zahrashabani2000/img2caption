from django.urls import path
from .views import ui, chat, new_chat

urlpatterns = [
    path('ui', ui, name='ui'),
    path('ui/', ui, name='ui-slash'),
    path('chat', chat, name='chat'),
    path('chat/', chat, name='chat-slash'),
    path('new_chat', new_chat, name='new_chat'),
    path('new_chat/', new_chat, name='new_chat-slash'),

]


