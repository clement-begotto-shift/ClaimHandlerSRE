from django.urls import path
from .views import ClaimHandlerView

urlpatterns = [
    path('get-claim', ClaimHandlerView.get, name='get-claim'),
    path('post-claims', ClaimHandlerView.post, name='post-claims'),
    # Add swagger
    # Add redoc
]