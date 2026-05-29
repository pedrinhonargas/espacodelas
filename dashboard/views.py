import csv
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import StreamingHttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from accounts.models import Professional, WorkingHours, BlockedSlot
from accounts.forms import BlockSlotForm, ProfessionalProfileForm, ServiceForm
from booking.models import Service, Appointment

# Helpers for Role Restrictions
def professional_or_owner_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'professional_profile'):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Acesso restrito a profissionais ou administradoras.")
    return _wrapped_view

def owner_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Acesso restrito à administradora.")
    return _wrapped_view


@login_required
def dashboard_home(request):
    """
    Redirects to the correct dashboard based on role.
    """
    if request.user.is_staff:
        return redirect('dashboard:owner')
    elif hasattr(request.user, 'professional_profile'):
        return redirect('dashboard:agenda')
    else:
        messages.error(request, "Seu usuário não possui perfil de profissional nem administrador.")
        return redirect('accounts:profile')


# ==========================================
# PROFESSIONAL DASHBOARD VIEWS
# ==========================================

@professional_or_owner_required
def agenda_view(request):
    # Parse date filter
    date_str = request.GET.get('data')
    if date_str:
        try:
            filter_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.localtime(timezone.now()).date()
    else:
        filter_date = timezone.localtime(timezone.now()).date()

    # Determine which professional's agenda to load
    is_owner = request.user.is_staff
    professionals = Professional.objects.filter(is_active=True)
    
    selected_prof_id = request.GET.get('profissional_id')
    
    if not is_owner:
        professional = request.user.professional_profile
        selected_prof_id = professional.id
    else:
        if selected_prof_id and selected_prof_id != 'all':
            professional = get_object_or_404(Professional, id=selected_prof_id)
        else:
            professional = None  # Owner wants to see all

    # Query appointments
    appointments_qs = Appointment.objects.filter(appointment_date=filter_date)
    if professional:
        appointments_qs = appointments_qs.filter(professional=professional)
    
    appointments = appointments_qs.order_by('appointment_time')

    # Compute quick stats
    total_appts = appointments.count()
    cancelled_appts = appointments.filter(status='cancelled').count()
    confirmed_appts = appointments.filter(status='confirmed').count()
    revenue = sum(app.service.price for app in appointments.filter(status='confirmed'))

    context = {
        'filter_date': filter_date,
        'appointments': appointments,
        'professionals': professionals,
        'selected_prof_id': selected_prof_id or 'all',
        'is_owner': is_owner,
        'professional': professional,
        'total_appts': total_appts,
        'cancelled_appts': cancelled_appts,
        'confirmed_appts': confirmed_appts,
        'revenue': revenue,
        'prev_date': (filter_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'next_date': (filter_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
    }
    return render(request, 'dashboard/agenda.html', context)


@professional_or_owner_required
def appointment_detail_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Restriction: professional can only see their own appointments
    if not request.user.is_staff:
        if appointment.professional != request.user.professional_profile:
            raise PermissionDenied("Você não tem permissão para visualizar este agendamento.")
            
    context = {
        'appointment': appointment,
        'is_owner': request.user.is_staff
    }
    return render(request, 'dashboard/appointment_detail.html', context)


@professional_or_owner_required
def cancel_by_professional_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Restriction
    if not request.user.is_staff:
        if appointment.professional != request.user.professional_profile:
            raise PermissionDenied("Você não tem permissão para cancelar este agendamento.")
            
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        # Trigger cancellation email tasks
        from booking.tasks import send_cancellation_email
        send_cancellation_email.delay(appointment.id)
        
        messages.success(request, "Agendamento cancelado com sucesso. A cliente foi notificada por e-mail.")
        return redirect('dashboard:agenda')
        
    return redirect('dashboard:appointment_detail', appointment_id=appointment.id)


@professional_or_owner_required
def block_slot_view(request):
    is_owner = request.user.is_staff
    
    if not is_owner:
        professional = request.user.professional_profile
    else:
        selected_prof_id = request.GET.get('profissional_id')
        if not selected_prof_id:
            messages.error(request, "Selecione um profissional para gerenciar bloqueios.")
            return redirect('dashboard:owner')
        professional = get_object_or_404(Professional, id=selected_prof_id)

    if request.method == 'POST':
        form = BlockSlotForm(request.POST)
        if form.is_valid():
            blocked_slot = form.save(commit=False)
            blocked_slot.professional = professional
            blocked_slot.save()
            messages.success(request, "Horário bloqueado com sucesso!")
            if is_owner:
                return redirect(f"/studio/bloquear/?profissional_id={professional.id}")
            return redirect('dashboard:block_slot')
    else:
        form = BlockSlotForm()

    # Load future blocks
    today = timezone.localtime(timezone.now()).date()
    blocked_slots = BlockedSlot.objects.filter(
        professional=professional,
        block_date__gte=today
    ).order_by('block_date', 'start_time')

    context = {
        'form': form,
        'blocked_slots': blocked_slots,
        'professional': professional,
        'is_owner': is_owner
    }
    return render(request, 'dashboard/block_slot.html', context)


@professional_or_owner_required
def remove_block_view(request, block_id):
    blocked_slot = get_object_or_404(BlockedSlot, id=block_id)
    
    # Restriction
    if not request.user.is_staff:
        if blocked_slot.professional != request.user.professional_profile:
            raise PermissionDenied("Sem permissão.")
            
    prof_id = blocked_slot.professional.id
    blocked_slot.delete()
    messages.success(request, "Bloqueio removido com sucesso.")
    
    if request.user.is_staff:
        return redirect(f"/studio/bloquear/?profissional_id={prof_id}")
    return redirect('dashboard:block_slot')


# ==========================================
# OWNER DASHBOARD VIEWS (Sprint 5)
# ==========================================

@owner_required
def owner_dashboard_view(request):
    today = timezone.localtime(timezone.now()).date()
    professionals = Professional.objects.filter(is_active=True)
    
    # Build data summaries
    prof_summaries = []
    for prof in professionals:
        appts = Appointment.objects.filter(professional=prof, appointment_date=today)
        confirmed = appts.filter(status='confirmed').count()
        cancelled = appts.filter(status='cancelled').count()
        revenue = sum(app.service.price for app in appts.filter(status='confirmed'))
        
        prof_summaries.append({
            'prof': prof,
            'confirmed': confirmed,
            'cancelled': cancelled,
            'revenue': revenue
        })
        
    # Global metrics
    month_start = today.replace(day=1)
    month_appts = Appointment.objects.filter(appointment_date__gte=month_start)
    total_month_bookings = month_appts.filter(status='confirmed').count()
    total_month_revenue = sum(app.service.price for app in month_appts.filter(status='confirmed'))
    
    context = {
        'today': today,
        'prof_summaries': prof_summaries,
        'total_month_bookings': total_month_bookings,
        'total_month_revenue': total_month_revenue
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


# Services CRUD
@owner_required
def service_list_view(request):
    services = Service.objects.all()
    return render(request, 'dashboard/services_list.html', {'services': services})


@owner_required
def service_create_view(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço cadastrado com sucesso!")
            return redirect('dashboard:services_list')
    else:
        form = ServiceForm()
    return render(request, 'dashboard/service_form.html', {'form': form, 'title': 'Cadastrar Novo Serviço'})


@owner_required
def service_update_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect('dashboard:services_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'dashboard/service_form.html', {'form': form, 'service': service, 'title': 'Editar Serviço'})


@owner_required
def service_toggle_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.is_active = not service.is_active
    service.save()
    status = "ativado" if service.is_active else "desativado"
    messages.success(request, f"Serviço '{service.name}' {status} com sucesso.")
    return redirect('dashboard:services_list')


# Professionals CRUD
@owner_required
def professional_list_view(request):
    professionals = Professional.objects.all()
    return render(request, 'dashboard/professionals_list.html', {'professionals': professionals})


@owner_required
def professional_create_view(request):
    if request.method == 'POST':
        # Need user fields plus professional fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        name = request.POST.get('name')
        role = request.POST.get('role')
        bio = request.POST.get('bio')
        photo = request.FILES.get('photo')
        
        if not username or not email or not name:
            messages.error(request, "Por favor, preencha os campos obrigatórios.")
            return render(request, 'dashboard/professional_form.html')
            
        try:
            with transaction.atomic():
                # Create django User
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Nome de usuário já cadastrado.")
                    return render(request, 'dashboard/professional_form.html')
                    
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='senha123',
                    first_name=name.split()[0]
                )
                
                # Create professional profile
                prof = Professional.objects.create(
                    user=user,
                    name=name,
                    role=role,
                    bio=bio,
                    photo=photo,
                    is_active=True
                )
                
                # Setup default working hours (Monday to Friday 9-19, Sat 9-17)
                for day in range(5):
                    WorkingHours.objects.create(
                        professional=prof,
                        weekday=day,
                        start_time=datetime.time(9, 0),
                        end_time=datetime.time(19, 0)
                    )
                WorkingHours.objects.create(
                    professional=prof,
                    weekday=5,
                    start_time=datetime.time(9, 0),
                    end_time=datetime.time(17, 0)
                )
                
            messages.success(request, f"Profissional cadastrada com sucesso! Usuário: {username} (Senha padrão: senha123)")
            return redirect('dashboard:professionals_list')
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar profissional: {str(e)}")
            
    return render(request, 'dashboard/professional_form.html', {'title': 'Cadastrar Nova Profissional'})


@owner_required
def professional_update_view(request, prof_id):
    professional = get_object_or_404(Professional, id=prof_id)
    if request.method == 'POST':
        form = ProfessionalProfileForm(request.POST, request.FILES, instance=professional)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil de profissional atualizado com sucesso!")
            return redirect('dashboard:professionals_list')
    else:
        form = ProfessionalProfileForm(instance=professional)
    return render(request, 'dashboard/professional_form.html', {'form': form, 'professional': professional, 'title': 'Editar Perfil Profissional'})


# Configuration of Grade
@owner_required
def working_hours_config_view(request, prof_id):
    professional = get_object_or_404(Professional, id=prof_id)
    
    # Load working hours for all days
    days = list(range(7))
    hours_dict = {h.weekday: h for h in WorkingHours.objects.filter(professional=professional)}
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for day in days:
                    is_active = request.POST.get(f'active_{day}') == 'on'
                    start_str = request.POST.get(f'start_{day}')
                    end_str = request.POST.get(f'end_{day}')
                    
                    if is_active and start_str and end_str:
                        start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
                        end_time = datetime.datetime.strptime(end_str, '%H:%M').time()
                        
                        if start_time >= end_time:
                            messages.error(request, f"O horário de início do dia {day} deve ser anterior ao de término.")
                            raise ValueError()
                            
                        WorkingHours.objects.update_or_create(
                            professional=professional,
                            weekday=day,
                            defaults={
                                'start_time': start_time,
                                'end_time': end_time,
                                'is_active': True
                            }
                        )
                    else:
                        # Deactivate or delete working hours for this day
                        WorkingHours.objects.filter(professional=professional, weekday=day).update(is_active=False)
                        
            messages.success(request, "Grade de horários atualizada com sucesso!")
            return redirect('dashboard:professionals_list')
        except ValueError:
            pass
        except Exception as e:
            messages.error(request, f"Erro ao atualizar grade: {str(e)}")

    working_days = []
    for day in days:
        existing = hours_dict.get(day)
        working_days.append({
            'weekday': day,
            'name': dict(WorkingHours.WEEKDAYS)[day],
            'is_active': existing.is_active if existing else False,
            'start_time': existing.start_time.strftime('%H:%M') if existing else '09:00',
            'end_time': existing.end_time.strftime('%H:%M') if existing else '19:00',
        })
        
    context = {
        'professional': professional,
        'working_days': working_days
    }
    return render(request, 'dashboard/working_hours.html', context)


# Reports
@owner_required
def report_view(request):
    professionals = Professional.objects.filter(is_active=True)
    
    # Query filters
    prof_id = request.GET.get('profissional_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    status = request.GET.get('status')
    
    appointments = Appointment.objects.all()
    
    if prof_id and prof_id != 'all':
        appointments = appointments.filter(professional_id=prof_id)
    if status and status != 'all':
        appointments = appointments.filter(status=status)
        
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__lte=end_date)
        except ValueError:
            pass
            
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    context = {
        'professionals': professionals,
        'appointments': appointments[:100],  # Limit grid to 100 for display
        'total_count': appointments.count(),
        'confirmed_count': appointments.filter(status='confirmed').count(),
        'revenue': sum(app.service.price for app in appointments.filter(status='confirmed')),
        'filter_prof_id': prof_id or 'all',
        'filter_status': status or 'all',
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'dashboard/report.html', context)


# Streaming CSV Export
class Echo:
    def write(self, value):
        return value

@owner_required
def export_csv_view(request):
    prof_id = request.GET.get('profissional_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    status = request.GET.get('status')
    
    appointments = Appointment.objects.all()
    
    if prof_id and prof_id != 'all':
        appointments = appointments.filter(professional_id=prof_id)
    if status and status != 'all':
        appointments = appointments.filter(status=status)
        
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date__lte=end_date)
        except ValueError:
            pass
            
    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    def csv_rows():
        writer = csv.writer(Echo())
        yield writer.writerow(['ID', 'Cliente', 'E-mail', 'WhatsApp', 'Serviço', 'Profissional', 'Data', 'Hora', 'Status', 'Valor (R$)'])
        for app in appointments:
            yield writer.writerow([
                app.id,
                app.client_name,
                app.client_email,
                app.client_phone,
                app.service.name,
                app.professional.name,
                app.appointment_date.strftime('%Y-%m-%d'),
                app.appointment_time.strftime('%H:%M'),
                app.get_status_display(),
                app.service.price
            ])

    response = StreamingHttpResponse(csv_rows(), content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="relatorio_agendamentos.csv"'
    return response
