from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Fuerza login para toda la aplicación excepto rutas públicas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_paths = [
            reverse("login"),
            reverse("logout"),
            "/admin/login/",
        ]

        if (
            not request.user.is_authenticated
            and not any(request.path.startswith(p) for p in public_paths)
        ):
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)
