from django.urls import path
from . import views
from accounts import views as accounts_views

app_name = 'dashboard'

urlpatterns = [
    # Auth
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    
    # Professional Dashboard
    path('', views.dashboard_home, name='home'),
    path('agenda/', views.agenda_view, name='agenda'),
    path('agendamento/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('agendamento/<int:appointment_id>/cancelar/', views.cancel_by_professional_view, name='cancel_appointment'),
    path('bloquear/', views.block_slot_view, name='block_slot'),
    path('bloquear/<int:block_id>/remover/', views.remove_block_view, name='remove_block'),
    path('perfil/', accounts_views.profile, name='profile'),
    
    # Owner Dashboard
    path('owner/', views.owner_dashboard_view, name='owner'),
    
    # Services Management
    path('servicos/', views.service_list_view, name='services_list'),
    path('servicos/novo/', views.service_create_view, name='service_create'),
    path('servicos/<int:service_id>/editar/', views.service_update_view, name='service_update'),
    path('servicos/<int:service_id>/toggle/', views.service_toggle_view, name='service_toggle'),
    
    # Professionals Management
    path('profissionais/', views.professional_list_view, name='professionals_list'),
    path('profissionais/novo/', views.professional_create_view, name='professional_create'),
    path('profissionais/<int:prof_id>/editar/', views.professional_update_view, name='professional_update'),
    
    # Working Hours Grade Configuration
    path('grade/<int:prof_id>/', views.working_hours_config_view, name='working_hours'),
    
    # Reports & Exports
    path('relatorios/', views.report_view, name='report'),
    path('relatorios/exportar/', views.export_csv_view, name='export_csv'),
]
