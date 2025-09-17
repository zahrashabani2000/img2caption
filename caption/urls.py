from django.urls import path
from .views import describe_image, ui

urlpatterns = [
    path('describe', describe_image, name='describe-image'),
    path('describe/', describe_image, name='describe-image-slash'),
    path('ui', ui, name='ui'),
    path('ui/', ui, name='ui-slash'),
]


