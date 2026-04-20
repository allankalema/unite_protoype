from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("accounts:login")

        profile = getattr(user, "profile", None)
        if not profile or profile.role != "staff":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("core:home")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
