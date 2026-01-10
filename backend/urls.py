from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# --- Add this configuration ---
schema_view = get_schema_view(
   openapi.Info(
      title="Mann's Portfolio Chatbot API",
      default_version='v1',
      description="API documentation for the portfolio chatbot and hiring form.",
      contact=openapi.Contact(email="mannavlakha1021@gmail.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
# --- End of configuration ---

# API v1 Versioning
v1_patterns = [
    path('', include('chatbot.urls')),
    path('projects/', include('projects.urls')),
    path('experience/', include('experience.urls')),
    path('health/', include('chatbot.health_urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Versioned API routes
    path('api/v1/', include((v1_patterns, 'chatbot_v1'), namespace='v1')),
    
    # Placeholder for v2
    # path('api/v2/', include('backend.v2_urls')), 

    # Compatibility: supporting old /api/ paths as well
    path('api/', include((v1_patterns, 'chatbot_compat'), namespace='compat')),
    
    # --- Corrected URL for the root path ---
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-ui'),
]