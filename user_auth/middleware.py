from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_access_time_str = request.session.get('last_access_time')

            if last_access_time_str:
                last_access_time = timezone.datetime.fromisoformat(
                    last_access_time_str)

                elapsed_time_seconds = (
                    timezone.now() - last_access_time).total_seconds()

                if elapsed_time_seconds > settings.SESSION_COOKIE_AGE:
                    # Session has expired, log the user out
                    current_user = request.user
                    if current_user.is_authenticated:
                        current_user.is_login_status = False
                        current_user.save()
                        logger.info(f"Session timeout for user: {request.user}")
                        logout(request)

            # Update the session with the current time as a string
            request.session['last_access_time'] = timezone.now().isoformat()

        response = self.get_response(request)
        return response


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