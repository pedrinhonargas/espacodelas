from django.contrib import admin
from .models import Professional, WorkingHours, BlockedSlot

class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 1
    classes = ['collapse']

class BlockedSlotInline(admin.TabularInline):
    model = BlockedSlot
    extra = 1
    classes = ['collapse']

@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'is_active', 'created_at')
    list_filter = ('is_active', 'role')
    search_fields = ('name', 'role', 'bio')
    inlines = [WorkingHoursInline, BlockedSlotInline]
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'role', 'photo', 'is_active')
        }),
        ('Informações Adicionais', {
            'classes': ('collapse',),
            'fields': ('bio',),
        }),
    )

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('professional', 'weekday', 'start_time', 'end_time', 'is_active')
    list_filter = ('professional', 'weekday', 'is_active')
    ordering = ('professional', 'weekday', 'start_time')

@admin.register(BlockedSlot)
class BlockedSlotAdmin(admin.ModelAdmin):
    list_display = ('professional', 'block_date', 'start_time', 'end_time', 'reason')
    list_filter = ('professional', 'block_date')
    search_fields = ('professional__name', 'reason')
