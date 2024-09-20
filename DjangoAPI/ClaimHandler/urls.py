from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import ClaimHandlerView


schema_view = get_schema_view(
   openapi.Info(
      title="Claim Handler API",
      default_version='v0',
      description="Handling claims",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('get-claim', ClaimHandlerView.get, name='get-claim'),
    path('post-claims', ClaimHandlerView.post, name='post-claims'),
    path('swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Add redoc
]