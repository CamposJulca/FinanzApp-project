from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    """
    Fuerza login para toda la aplicación excepto rutas públicas y archivos estáticos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # 🔓 Rutas que NO requieren autenticación
        public_paths = [
            reverse("login"),
            reverse("logout"),
            "/admin/login/",
            "/admin/",
            "/assets/",
            "/static/",
        ]

        # Permitir archivos estáticos directamente
        if any(request.path.startswith(p) for p in ["/assets/", "/static/"]):
            return self.get_response(request)

        # Forzar autenticación
        if (
            not request.user.is_authenticated
            and not any(request.path.startswith(p) for p in public_paths)
        ):
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)
