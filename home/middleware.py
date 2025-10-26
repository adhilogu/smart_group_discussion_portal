from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseForbidden


class OneSessionPerUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get all sessions for current user
            current_session_key = request.session.session_key

            # Delete other sessions for this user
            user_sessions = Session.objects.filter(
                expire_date__gt=timezone.now()
            )

            for session in user_sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(
                        request.user.id) and session.session_key != current_session_key:
                    session.delete()

        response = self.get_response(request)
        return response

class PasswordBlockerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the URL contains password-related terms
        path = request.path.lower()
        if '/accounts/' in path and ('password' in path or 'passwd' in path or 'reset' in path):
            return HttpResponseForbidden("Password reset functionality is disabled.")
        return self.get_response(request)

class BlockSignupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/accounts/signup/':
            from django.shortcuts import redirect
            return redirect('/')  # Redirect to home page
        return self.get_response(request)