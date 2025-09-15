from django.contrib import admin
from django.urls import path, include
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





urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chatbot.urls')),
    path('vishal/', include('vishal.urls')),
    
    # --- Corrected URL for the root path ---
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-ui'),
]