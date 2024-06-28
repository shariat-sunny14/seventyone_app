from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from functools import wraps
from django.shortcuts import redirect

def login_required_with_timeout(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        last_access_time_str = request.session.get('last_access_time')

        if last_access_time_str:
            last_access_time = timezone.datetime.fromisoformat(last_access_time_str)
            elapsed_time_seconds = (timezone.now() - last_access_time).total_seconds()

            if elapsed_time_seconds > settings.SESSION_COOKIE_AGE:
                # Update the user's login status to False upon logout
                current_user = request.user
                if current_user.is_authenticated:
                    current_user.is_login_status = False
                    current_user.save()
                logout(request)
                return redirect('login')

        request.session['last_access_time'] = timezone.now().isoformat()
        return view_func(request, *args, **kwargs)

    return _wrapped_view



"""
for auto logout use this code
#settings.py
SESSION_COOKIE_AGE = 1800  # 1800 seconds (30 minutes)
MIDDLEWARE = [
    'user_auth.middleware.SessionTimeoutMiddleware',  # Make sure this path is correct
]

#middleware.py
#decorators.py

use this python file or function
"""