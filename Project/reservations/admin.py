from django.contrib import admin
from .models import Reservation, ReservationItem

class ReservationItemInline(admin.TabularInline):
    model = ReservationItem
    extra = 1

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reservation_date', 'start_date', 'end_date', 'status', 'total_cost')
    list_filter = ('status', 'reservation_date')
    search_fields = ('user__username', 'user__email')
    inlines = [ReservationItemInline]

@admin.register(ReservationItem)
class ReservationItemAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'item', 'quantity', 'price_per_day', 'subtotal')
    list_filter = ('reservation__status',)
    search_fields = ('item__name', 'reservation__user__username')
