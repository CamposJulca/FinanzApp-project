from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # API
    path("api/transactions/", include("transactions.urls")),


    # Frontend
    path("", RedirectView.as_view(url="/transacciones/", permanent=False)),

    # La SPA maneja sus propias subrutas (/transacciones/cuentas, etc.).
    # El catch-all devuelve index.html para que recargar o entrar directo a un
    # módulo no acabe en un 404 de Django.
    re_path(
        r"^transacciones/.*$",
        TemplateView.as_view(template_name="index.html"),
        name="spa",
    ),
]


# Servir archivos estáticos de Vite en desarrollo
# (/assets/*)
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0],
    )
