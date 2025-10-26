from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.authtoken.views import obtain_auth_token
from django.views.defaults import permission_denied

# Common error message for password-related functionality
password_error = Exception('Password reset/change functionality is disabled')

urlpatterns = [
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('', include('admin_datta.urls')),
    path('', include('django_dyn_dt.urls')),  # Dynamic_DT Routing

    # Block signup URLs
    path('accounts/signup/',
         permission_denied,
         {'exception': Exception('Signup not allowed')},
         name='account_signup'),
    path('accounts/signup/closed/',
         permission_denied,
         {'exception': Exception('Signup not allowed')},
         name='account_signup_closed'),
    path('accounts/3rdparty/signup/',
         permission_denied,
         {'exception': Exception('Signup not allowed')}),
    re_path(r'^accounts/.*signup.*',
            permission_denied,
            {'exception': Exception('Signup not allowed')}),

    # Block ALL password-related URLs with multiple patterns
    # Standard Django auth patterns
    re_path(r'^accounts/password-reset/?.*',
            permission_denied,
            {'exception': password_error}),
    re_path(r'^accounts/password/reset/?.*',
            permission_denied,
            {'exception': password_error}),
    re_path(r'^reset/.*',
            permission_denied,
            {'exception': password_error}),

    # More general patterns to catch any password-related URL
    re_path(r'^accounts/.*password.*',
            permission_denied,
            {'exception': password_error}),
    re_path(r'^accounts/.*reset.*',
            permission_denied,
            {'exception': password_error}),

    # Include remaining allauth URLs (after blocking specific ones)
    path('accounts/', include('allauth.urls')),
]

# Lazy-load API routes
try:
    urlpatterns += [
        path('api/', include('api.urls')),
        path('login/jwt/', obtain_auth_token),
    ]
except Exception as e:
    import logging

    logging.warning(f"Error loading API routes: {e}")