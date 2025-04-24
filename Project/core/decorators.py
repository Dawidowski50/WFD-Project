from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from functools import wraps

def manager_required(view_func):
    def check_manager(user):
        return user.is_authenticated and user.userprofile.role in ['manager', 'admin']
    return user_passes_test(check_manager)(view_func)

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.userprofile.role in ['staff', 'manager', 'admin']:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Access denied")
    return _wrapped_view

def customer_required(view_func):
    def check_customer(user):
        return user.is_authenticated and user.userprofile.role == 'customer'
    return user_passes_test(check_customer)(view_func) 