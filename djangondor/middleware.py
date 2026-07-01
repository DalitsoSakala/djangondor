import contextvars

# contextvars is used instead of threading.local since it also works correctly under async views
_current_user = contextvars.ContextVar("current_user", default=None)


class CurrentUserMiddleware:
    """Stashes the authenticated user for the duration of the request so model-layer
    code (`AuditLogMixin`) can read who is making a change without every `save()` call
    having to be passed a user explicitly.

    Add this **after** `django.contrib.auth.middleware.AuthenticationMiddleware` in
    `MIDDLEWARE`::

        MIDDLEWARE = [
            ...,
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "djangondor.middleware.CurrentUserMiddleware",
            ...,
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_user.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            _current_user.reset(token)


def get_current_user():
    """Returns the currently authenticated user for this request, or `None` if there
    isn't one (no request in progress, or the user isn't authenticated)."""
    user = _current_user.get()
    return user if getattr(user, "is_authenticated", False) else None
