"""
This module was created and tested with Python 3.11.

URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from identity.views import upload_identity, verification_detail, privacy_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload/', upload_identity, name='upload'),
    path('verification/<uuid:pk>/', verification_detail, name='verification_detail'),
    path('privacy/', privacy_view, name='privacy'),
]

# This is only for development; in production, serve media files through a proper web server
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
