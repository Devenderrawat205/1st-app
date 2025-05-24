# BQ/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Keep for static files during DEBUG
from django.conf.urls.static import static  # Keep for static files during DEBUG
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Let Researchers.urls handle the root and other app-specific URLs
    # The 'researchers' namespace here means you'll use {% url 'researchers:url_name' %} in templates
    path('', include('Researchers.urls', namespace='researchers')),

    # Redirect /favicon.ico to /static/favicon.ico if your favicon is in project's static/
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
]

# This part is for serving static files during development ONLY
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0])
    # Using STATIC_ROOT is more robust if you define it, otherwise fall back to STATICFILES_DIRS[0]
    # Ensure STATIC_URL ends with a slash, and STATICFILES_DIRS[0] is correctly your project's static folder