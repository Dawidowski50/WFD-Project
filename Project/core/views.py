from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from datetime import datetime
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from inventory.models import Category, Item, Maintenance
from reservations.models import Reservation, ReservationItem
from .models import UserProfile
from .forms import MaintenanceForm
from .decorators import manager_required, staff_required

User = get_user_model()

# Permission check functions
def is_staff_or_manager(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role in ['staff', 'manager', 'admin']

def is_manager(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role in ['manager', 'admin']

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

# Public views
@login_required
def home(request):
    # Display home page with available items
    categories = Category.objects.all()
    items = Item.objects.filter(is_available=True)
    return render(request, 'core/home.html', {
        'categories': categories,
        'items': items
    })

def catalog(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    
    items = Item.objects.all()
    if category_id:
        items = items.filter(category_id=category_id)
    
    context = {
        'categories': categories,
        'items': items,
        'selected_category': category_id,
        'today': timezone.now().date()
    }
    return render(request, 'core/catalog.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')

# Customer views
@login_required
def reserve_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not all([start_date, end_date]):
            messages.error(request, 'Please provide both start and end dates.')
            return redirect('catalog')
        
        try:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            
            if start_date.date() < timezone.now().date():
                messages.error(request, 'Start date cannot be in the past.')
                return redirect('catalog')
            
            if end_date.date() < start_date.date():
                messages.error(request, 'End date must be after start date.')
                return redirect('catalog')
            
            if Maintenance.objects.filter(
                item=item,
                maintenance_date__range=(start_date, end_date),
                status__in=['SCHEDULED', 'IN_PROGRESS']
            ).exists():
                messages.error(request, 'Item is scheduled for maintenance during the selected dates.')
                return redirect('catalog')
            
            if ReservationItem.objects.filter(
                item=item,
                reservation__start_date__lte=end_date,
                reservation__end_date__gte=start_date,
                reservation__status='active'
            ).exists():
                messages.error(request, 'Item is already reserved for the selected dates.')
                return redirect('catalog')
            
            days = (end_date - start_date).days + 1
            total_cost = item.daily_rate * Decimal(str(days))
            
            with transaction.atomic():
                reservation = Reservation.objects.create(
                    user=request.user,
                    start_date=start_date,
                    end_date=end_date,
                    status='active',
                    total_cost=total_cost
                )
                
                ReservationItem.objects.create(
                    reservation=reservation,
                    item=item,
                    price_per_day=item.daily_rate,
                    subtotal=total_cost
                )
            
            messages.success(request, f'Successfully reserved {item.name}')
            return redirect('my_reservations')
            
        except ValueError:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            return redirect('catalog')
    
    return redirect('catalog')

@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_reservations.html', {'reservations': reservations})

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if reservation.status == 'cancelled':
        messages.warning(request, 'This reservation is already cancelled.')
    else:
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, 'Reservation cancelled successfully.')
    
    return redirect('my_reservations')

# Staff views
@login_required
@user_passes_test(is_staff_or_manager, login_url=None, redirect_field_name=None)
def process_return(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status == 'completed':
            reservation.status = 'completed'
            reservation.save()
            
            for reservation_item in reservation.items.all():
                item = reservation_item.item
                item.is_available = True
                item.save()
            
            messages.success(request, 'Equipment return processed successfully.')
        return redirect('manage_returns')
    
    return render(request, 'core/process_return.html', {'reservation': reservation})

@login_required
@user_passes_test(is_staff_or_manager, login_url=None, redirect_field_name=None)
def manage_returns(request):
    active_returns = Reservation.objects.filter(
        status='pending',
        end_date__lte=timezone.now()
    ).order_by('-end_date')
    
    return render(request, 'core/manage_returns.html', {
        'active_returns': active_returns
    })

@manager_required
def schedule_maintenance(request, item_id=None):
    if item_id:
        item = get_object_or_404(Item, id=item_id)
    else:
        item = None
    
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.staff = request.user
            maintenance.save()
            
            messages.success(request, 'Maintenance scheduled successfully')
            return redirect('maintenance_schedule')
    else:
        initial = {}
        if item:
            initial['item'] = item
        form = MaintenanceForm(initial=initial)
    
    return render(request, 'core/schedule_maintenance.html', {
        'form': form,
        'item': item
    })

def staff_or_manager_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_staff_or_manager(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@staff_or_manager_required
@require_http_methods(['GET', 'POST'])
def view_maintenance_schedule(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        maintenance_id = request.POST.get('maintenance_id')
        
        if action == 'update_status' and maintenance_id:
            try:
                maintenance = Maintenance.objects.get(id=maintenance_id)
                new_status = request.POST.get('status')
                if new_status in ['SCHEDULED', 'IN_PROGRESS', 'COMPLETED']:
                    maintenance.status = new_status
                    maintenance.save()
                    messages.success(request, f'Maintenance status updated to {new_status}.')
            except Maintenance.DoesNotExist:
                messages.error(request, 'Maintenance record not found.')
        
        return redirect('maintenance_schedule')
    
    maintenance_list = Maintenance.objects.all().order_by('maintenance_date')
    # Get all items that are available for maintenance
    available_items = Item.objects.filter(is_available=True).order_by('name')
    
    # Check if user is a manager through their profile
    is_manager = request.user.userprofile.role == 'manager'
    
    # If user is a manager, calculate analytics
    if is_manager:
        total_records = maintenance_list.count()
        pending_count = maintenance_list.filter(status='pending').count()
        in_progress_count = maintenance_list.filter(status='in_progress').count()
        completed_count = maintenance_list.filter(status='completed').count()
        completion_rate = (completed_count / total_records * 100) if total_records > 0 else 0
        
        analytics = {
            'total_records': total_records,
            'pending_count': pending_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'completion_rate': completion_rate
        }
    else:
        analytics = None
    
    return render(request, 'core/maintenance_schedule.html', {
        'maintenance_records': maintenance_list,
        'available_items': available_items,
        'is_manager': is_manager,
        'analytics': analytics
    })

# Manager views
@login_required
@user_passes_test(is_manager, login_url=None, redirect_field_name=None)
def manage_inventory(request):
    items = Item.objects.all().order_by('category', 'name')
    categories = Category.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                name = request.POST.get('name')
                category_id = request.POST.get('category')
                daily_rate = request.POST.get('daily_rate')
                description = request.POST.get('description')
                condition = request.POST.get('condition')
                
                if not all([name, category_id, daily_rate, description, condition]):
                    messages.error(request, 'Please fill all required fields.')
                    return redirect('manage_inventory')
                
                category = get_object_or_404(Category, id=category_id)
                
                Item.objects.create(
                    name=name,
                    category=category,
                    daily_rate=daily_rate,
                    description=description,
                    condition=condition,
                    is_available=True
                )
                messages.success(request, f'Item "{name}" added successfully.')
            except Exception as e:
                messages.error(request, f'Error adding item: {str(e)}')
            
            return redirect('manage_inventory')
        
        elif action == 'edit':
            try:
                item_id = request.POST.get('item_id')
                name = request.POST.get('name')
                category_id = request.POST.get('category')
                daily_rate = request.POST.get('daily_rate')
                description = request.POST.get('description')
                condition = request.POST.get('condition')
                
                if not all([item_id, name, category_id, daily_rate, description, condition]):
                    messages.error(request, 'Please fill all required fields.')
                    return redirect('manage_inventory')
                
                item = get_object_or_404(Item, id=item_id)
                category = get_object_or_404(Category, id=category_id)
                
                item.name = name
                item.category = category
                item.daily_rate = daily_rate
                item.description = description
                item.condition = condition
                item.save()
                
                messages.success(request, f'Item "{name}" updated successfully.')
            except Exception as e:
                messages.error(request, f'Error updating item: {str(e)}')
            
            return redirect('manage_inventory')
        
        elif action == 'delete':
            try:
                item = get_object_or_404(Item, id=request.POST.get('item_id'))
                name = item.name
                item.delete()
                messages.success(request, f'Item "{name}" deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting item: {str(e)}')
            
            return redirect('manage_inventory')
    
    return render(request, 'core/manage_inventory.html', {
        'items': items,
        'categories': categories
    })

@login_required
@user_passes_test(is_manager, login_url=None, redirect_field_name=None)
def manage_categories(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_category':
            name = request.POST.get('name')
            description = request.POST.get('description')
            Category.objects.create(name=name, description=description)
            messages.success(request, 'Category added successfully.')
            
        elif action == 'edit_category':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            category = get_object_or_404(Category, id=category_id)
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Category updated successfully.')
            
        elif action == 'delete_category':
            category_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=category_id)
                if category.items.exists():
                    messages.error(request, 'Cannot delete category that has items. Please remove or reassign items first.')
                else:
                    category.delete()
                    messages.success(request, 'Category deleted successfully.')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
    
    return render(request, 'core/manage_categories.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_manager)
def manage_staff(request):
    is_admin_user = request.user.userprofile.role == 'admin'
    is_manager_user = request.user.userprofile.role == 'manager'

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_staff' and (is_admin_user or is_manager_user):
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            
            if not all([username, email, password, role]):
                messages.error(request, 'All fields are required.')
                return redirect('manage_staff')
            
            if not is_admin_user and role in ['admin', 'manager']:
                messages.error(request, 'Managers can only create staff users.')
                return redirect('manage_staff')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('manage_staff')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('manage_staff')
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    user.is_staff = True
                    user.is_superuser = (role == 'admin')
                    user.save()
                    
                    if not hasattr(user, 'userprofile'):
                        UserProfile.objects.create(
                            user=user,
                            role=role
                        )
                    else:
                        user.userprofile.role = role
                        user.userprofile.save()
                    
                    messages.success(request, f'Staff member {username} has been added successfully.')
            except Exception as e:
                messages.error(request, f'Error creating staff member: {str(e)}')
            
            return redirect('manage_staff')
        
        elif action == 'update_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')
            
            try:
                user = User.objects.get(id=user_id)
                if user != request.user:
                    if new_role == 'admin' and not is_admin_user:
                        messages.error(request, 'Only administrators can assign admin roles.')
                    elif user.userprofile.role == 'admin' and not is_admin_user:
                        messages.error(request, 'Only administrators can modify admin users.')
                    elif not is_admin_user and new_role == 'manager':
                        messages.error(request, 'Only administrators can assign manager roles.')
                    else:
                        with transaction.atomic():
                            user.is_staff = True
                            user.is_superuser = (new_role == 'admin')
                            user.save()
                            
                            profile = user.userprofile
                            profile.role = new_role
                            profile.save()
                            
                            messages.success(request, f'Role updated for {user.username}.')
                else:
                    messages.error(request, 'You cannot modify your own role.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
            except Exception as e:
                messages.error(request, f'Error updating role: {str(e)}')
            
            return redirect('manage_staff')
        
        elif action == 'delete_staff':
            user_id = request.POST.get('user_id')
            
            try:
                user = User.objects.get(id=user_id)
                if user.userprofile.role == 'admin' and not is_admin_user:
                    messages.error(request, 'Only administrators can delete admin users.')
                elif not is_admin_user and user.userprofile.role == 'manager':
                    messages.error(request, 'Only administrators can delete managers.')
                elif user != request.user:
                    username = user.username
                    user.delete()
                    messages.success(request, f'Staff member {username} has been deleted.')
                else:
                    messages.error(request, 'You cannot delete your own account.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
            except Exception as e:
                messages.error(request, f'Error deleting staff member: {str(e)}')
            
            return redirect('manage_staff')
    
    staff_users = User.objects.filter(is_staff=True).exclude(id=request.user.id).prefetch_related('userprofile')
    
    if not is_admin_user:
        staff_users = staff_users.exclude(userprofile__role='admin')
        if not is_manager_user:
            staff_users = staff_users.exclude(userprofile__role='manager')
    
    return render(request, 'core/manage_staff.html', {
        'staff_users': staff_users,
        'is_admin_user': is_admin_user,
        'is_manager_user': is_manager_user
    })

@login_required
def generate_reports(request):
    if not is_manager(request.user):
        return HttpResponseForbidden('You do not have permission to access this page.')
        
    items = Item.objects.all()
    total_items = items.count()
    available_items = items.filter(is_available=True).count()
    active_reservations = Reservation.objects.filter(status='active').count()
    
    in_maintenance = Item.objects.filter(
        maintenance_records__status__in=['pending', 'in_progress'],
        maintenance_records__maintenance_date__date=timezone.now().date()
    ).distinct().count()
    
    pending_returns = Reservation.objects.filter(
        status='active',
        end_date__lte=timezone.now().date()
    ).count()
    
    categories = Category.objects.all()
    category_stats = []
    
    for category in categories:
        cat_items = items.filter(category=category)
        total = cat_items.count()
        available = cat_items.filter(is_available=True).count()
        in_use = cat_items.filter(
            reservationitem__reservation__status='active',
            reservationitem__reservation__start_date__lte=timezone.now().date(),
            reservationitem__reservation__end_date__gte=timezone.now().date()
        ).distinct().count()
        in_maintenance = cat_items.filter(
            maintenance_records__status__in=['pending', 'in_progress'],
            maintenance_records__maintenance_date__date=timezone.now().date()
        ).distinct().count()
        
        category_stats.append({
            'name': category.name,
            'total': total,
            'available': available,
            'in_use': in_use,
            'in_maintenance': in_maintenance
        })
    
    return render(request, 'core/reports.html', {
        'total_items': total_items,
        'available_items': available_items,
        'active_reservations': active_reservations,
        'in_maintenance': in_maintenance,
        'pending_returns': pending_returns,
        'category_stats': category_stats
    })
