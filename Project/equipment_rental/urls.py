"""
URL configuration for equipment_rental project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    home, catalog, reserve_item, my_reservations, cancel_reservation,
    manage_inventory, manage_categories, manage_staff, manage_returns,
    process_return, schedule_maintenance, view_maintenance_schedule,
    generate_reports, logout_view
)
from users.views import login_view

# Override admin login
admin.site.login = login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('catalog/', catalog, name='catalog'),
    path('reserve/<int:item_id>/', reserve_item, name='reserve_item'),
    path('my-reservations/', my_reservations, name='my_reservations'),
    path('cancel-reservation/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
    path('inventory/', manage_inventory, name='manage_inventory'),
    path('categories/', manage_categories, name='manage_categories'),
    path('staff/', manage_staff, name='manage_staff'),
    path('returns/', manage_returns, name='manage_returns'),
    path('process-return/<int:reservation_id>/', process_return, name='process_return'),
    path('maintenance/schedule/', view_maintenance_schedule, name='maintenance_schedule'),
    path('maintenance/schedule/new/', schedule_maintenance, name='schedule_maintenance_new'),
    path('maintenance/schedule/<int:item_id>/', schedule_maintenance, name='schedule_maintenance_item'),
    path('reports/', generate_reports, name='reports'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
