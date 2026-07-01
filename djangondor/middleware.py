import contextvars
from contextlib import contextmanager
from types import SimpleNamespace

# contextvars is used instead of threading.local since it also works correctly under async views
_current_request = contextvars.ContextVar("current_request", default=None)


class CurrentUserMiddleware:
    """Stashes the in-flight request for the duration of the response so model-layer
    code (`AuditLogMixin`) can read who is making a change without every `save()` call
    having to be passed a user explicitly.

    Stores the *request*, not `request.user`, and `get_current_user()` reads
    `request.user` fresh each time it's called rather than snapshotting it up front.
    This matters for DRF (and anything else that authenticates inside the view): DRF's
    `TokenAuthentication`/JWT/etc. run in `perform_authentication()`, which happens
    *inside* `dispatch()` — i.e. after this middleware has already started
    `get_response(request)`. Snapshotting `request.user` before that point would only
    ever see the session-based value (usually `AnonymousUser`), not the
    DRF-authenticated one. By the time a view's model code calls `save()`, DRF has
    already replaced `request.user`, so reading it lazily gets the right value.

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
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)


def get_current_user():
    """Returns the currently authenticated user for the in-flight request, or `None`
    if there isn't one (no request in progress, or the user isn't authenticated)."""
    user = getattr(_current_request.get(), "user", None)
    return user if getattr(user, "is_authenticated", False) else None


@contextmanager
def run_as(user):
    """Attribute audit log entries to `user` outside of a request — management
    commands, the shell, background tasks — where there's no
    `CurrentUserMiddleware` to set the acting user automatically::

        from djangondor.middleware import run_as

        with run_as(some_user):
            Article.objects.create(...)  # AuditLog rows attribute to some_user
    """
    token = _current_request.set(SimpleNamespace(user=user))
    try:
        yield
    finally:
        _current_request.reset(token)
