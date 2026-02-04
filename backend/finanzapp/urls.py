from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # APIs
    path("api/", include("transactions.urls")),

    # Frontend React (Vite build)
    # Captura / y cualquier ruta no-API y no-admin
    path("", TemplateView.as_view(template_name="index.html")),
]

# Servir archivos estáticos de Vite en desarrollo
# (/assets/*)
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0],
    )
