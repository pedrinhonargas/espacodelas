from django.contrib import admin
from .models import Service, ProfessionalService, Appointment, EmailLog

class ProfessionalServiceInline(admin.TabularInline):
    model = ProfessionalService
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_minutes', 'price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    inlines = [ProfessionalServiceInline]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_phone', 'professional', 'service', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'professional', 'service', 'appointment_date')
    search_fields = ('client_name', 'client_email', 'client_phone', 'professional__name', 'service__name')
    date_hierarchy = 'appointment_date'
    actions = ['make_confirmed', 'make_cancelled', 'make_pending']

    def make_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    make_confirmed.short_description = "Marcar selecionados como Confirmados"

    def make_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    make_cancelled.short_description = "Marcar selecionados como Cancelados"

    def make_pending(self, request, queryset):
        queryset.update(status='pending')
    make_pending.short_description = "Marcar selecionados como Pendentes"

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'email_type', 'recipient_email', 'sent_success', 'sent_at')
    list_filter = ('email_type', 'sent_success', 'sent_at')
    search_fields = ('recipient_email', 'appointment__client_name')
    readonly_fields = ('appointment', 'email_type', 'recipient_email', 'sent_success', 'sent_at')
