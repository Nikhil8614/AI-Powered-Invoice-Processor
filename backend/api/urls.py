from django.urls import path
from .views import upload_invoice  # Import your view function

urlpatterns = [
    path('api/upload-invoice/', upload_invoice, name='upload-invoice'),
]
