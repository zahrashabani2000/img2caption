from django.urls import path
from .views import describe_image, ui, generate_image

urlpatterns = [
    path('describe', describe_image, name='describe-image'),
    path('describe/', describe_image, name='describe-image-slash'),
    path('generate', generate_image, name='generate-image'),
    path('generate/', generate_image, name='generate-image-slash'),
    path('ui', ui, name='ui'),
    path('ui/', ui, name='ui-slash'),
]


