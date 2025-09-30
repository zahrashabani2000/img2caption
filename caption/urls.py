from django.urls import path
from .views import ui, generate_image, chat

urlpatterns = [
    path('generate', generate_image, name='generate-image'),
    path('generate/', generate_image, name='generate-image-slash'),
    path('ui', ui, name='ui'),
    path('ui/', ui, name='ui-slash'),
    path('chat', chat, name='chat'),
    path('chat/', chat, name='chat-slash'),
]


