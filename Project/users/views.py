from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.template.context_processors import csrf
from django.middleware.csrf import get_token
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.

@csrf_protect
def login_view(request):
    context = {}
    context.update(csrf(request))
    
    # Ensure CSRF token is set in cookie
    get_token(request)
    
    # Check if this is an admin login attempt
    is_admin_login = request.path.startswith('/admin/')
    
    if request.method == 'POST':
        email = request.POST.get('username')  # The form field is still named 'username'
        password = request.POST.get('password')
        
        # Try to authenticate with email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            # Ensure user profile exists
            if not hasattr(user, 'userprofile'):
                from core.models import UserProfile
                role = 'admin' if user.is_superuser else 'staff' if user.is_staff else 'customer'
                UserProfile.objects.create(user=user, role=role)
            # Set user's role in session
            request.session['user_role'] = user.userprofile.role
            # Handle next parameter
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            elif is_admin_login and user.is_staff:
                return redirect('admin:index')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
    
    # Add next parameter to context if it exists
    next_url = request.GET.get('next')
    if next_url:
        context['next'] = next_url
    
    # Use admin login template for admin login
    template_name = 'admin/login.html' if is_admin_login else 'registration/login.html'
    return render(request, template_name, context)
