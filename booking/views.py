import datetime
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from accounts.models import Professional, WorkingHours
from booking.models import Service, Appointment
from .forms import BookingForm
from .utils import get_available_slots, get_available_slots_no_preference, get_available_dates

class BookingStep1View(View):
    def get(self, request):
        services = Service.objects.filter(is_active=True)
        professionals = Professional.objects.filter(is_active=True)
        
        # Check URL query params for pre-selections
        pre_service_id = request.GET.get('servico')
        pre_prof_id = request.GET.get('profissional')
        
        context = {
            'services': services,
            'professionals': professionals,
            'pre_service_id': pre_service_id,
            'pre_prof_id': pre_prof_id,
            'step': 1
        }
        return render(request, 'booking/step1.html', context)

    def post(self, request):
        service_id = request.POST.get('service')
        professional_id = request.POST.get('professional')
        
        if not service_id:
            messages.error(request, "Por favor, selecione um serviço.")
            return redirect('booking:start')
            
        request.session['booking_service_id'] = service_id
        request.session['booking_professional_id'] = professional_id or 'none'
        
        return redirect('booking:step2')


class BookingStep2View(View):
    def get(self, request):
        service_id = request.session.get('booking_service_id')
        professional_id = request.session.get('booking_professional_id')
        
        if not service_id:
            messages.warning(request, "Por favor, selecione o serviço primeiro.")
            return redirect('booking:start')
            
        service = get_object_or_404(Service, id=service_id)
        
        professional = None
        if professional_id and professional_id != 'none':
            professional = get_object_or_404(Professional, id=professional_id)
            
        # Get active dates with availability (for calendar high-lighting)
        available_dates = get_available_dates(service, professional)
        
        context = {
            'service': service,
            'professional': professional,
            'available_dates_json': available_dates,
            'step': 2
        }
        return render(request, 'booking/step2.html', context)

    def post(self, request):
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        if not date_str or not time_str:
            messages.error(request, "Por favor, escolha uma data e um horário.")
            return redirect('booking:step2')
            
        request.session['booking_date'] = date_str
        request.session['booking_time'] = time_str
        
        return redirect('booking:step3')


class BookingSlotsAjaxView(View):
    def get(self, request):
        date_str = request.GET.get('data')
        service_id = request.session.get('booking_service_id') or request.GET.get('servico_id')
        professional_id = request.session.get('booking_professional_id') or request.GET.get('profissional_id')
        
        if not date_str or not service_id:
            return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
            
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            service = Service.objects.get(id=service_id)
        except (ValueError, Service.DoesNotExist):
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
            
        if professional_id and professional_id != 'none':
            try:
                prof = Professional.objects.get(id=professional_id)
                slots = get_available_slots(prof, service, date)
            except Professional.DoesNotExist:
                return JsonResponse({'error': 'Profissional não encontrado'}, status=400)
        else:
            slots, _ = get_available_slots_no_preference(service, date)
            
        # Return time strings HH:MM
        slots_json = [s.strftime('%H:%M') for s in slots]
        return JsonResponse({'slots': slots_json})


class BookingStep3View(View):
    def get(self, request):
        service_id = request.session.get('booking_service_id')
        professional_id = request.session.get('booking_professional_id')
        date_str = request.session.get('booking_date')
        time_str = request.session.get('booking_time')
        
        if not all([service_id, professional_id, date_str, time_str]):
            messages.warning(request, "Sua sessão expirou ou o fluxo está incompleto. Recomece o agendamento.")
            return redirect('booking:start')
            
        service = get_object_or_404(Service, id=service_id)
        professional = None
        if professional_id != 'none':
            professional = get_object_or_404(Professional, id=professional_id)
            
        form = BookingForm(initial={
            'client_name': request.session.get('booking_client_name', ''),
            'client_email': request.session.get('booking_client_email', ''),
            'client_phone': request.session.get('booking_client_phone', '')
        })
        
        context = {
            'service': service,
            'professional': professional,
            'date': datetime.datetime.strptime(date_str, '%Y-%m-%d').date(),
            'time': time_str,
            'form': form,
            'step': 3
        }
        return render(request, 'booking/step3.html', context)

    def post(self, request):
        form = BookingForm(request.POST)
        if form.is_valid():
            request.session['booking_client_name'] = form.cleaned_data['client_name']
            request.session['booking_client_email'] = form.cleaned_data['client_email']
            request.session['booking_client_phone'] = form.cleaned_data['client_phone']
            return redirect('booking:confirm')
            
        # If invalid, re-render
        service_id = request.session.get('booking_service_id')
        professional_id = request.session.get('booking_professional_id')
        date_str = request.session.get('booking_date')
        time_str = request.session.get('booking_time')
        
        service = get_object_or_404(Service, id=service_id)
        professional = None
        if professional_id != 'none':
            professional = get_object_or_404(Professional, id=professional_id)
            
        context = {
            'service': service,
            'professional': professional,
            'date': datetime.datetime.strptime(date_str, '%Y-%m-%d').date(),
            'time': time_str,
            'form': form,
            'step': 3
        }
        return render(request, 'booking/step3.html', context)


class BookingConfirmView(View):
    def get(self, request):
        service_id = request.session.get('booking_service_id')
        professional_id = request.session.get('booking_professional_id')
        date_str = request.session.get('booking_date')
        time_str = request.session.get('booking_time')
        client_name = request.session.get('booking_client_name')
        client_email = request.session.get('booking_client_email')
        client_phone = request.session.get('booking_client_phone')
        
        if not all([service_id, professional_id, date_str, time_str, client_name, client_email, client_phone]):
            messages.warning(request, "Sua sessão expirou ou o fluxo está incompleto. Recomece o agendamento.")
            return redirect('booking:start')
            
        service = get_object_or_404(Service, id=service_id)
        professional = None
        if professional_id != 'none':
            professional = get_object_or_404(Professional, id=professional_id)
            
        context = {
            'service': service,
            'professional': professional,
            'date': datetime.datetime.strptime(date_str, '%Y-%m-%d').date(),
            'time': time_str,
            'client_name': client_name,
            'client_email': client_email,
            'client_phone': client_phone,
            'step': 4
        }
        return render(request, 'booking/confirm.html', context)

    def post(self, request):
        service_id = request.session.get('booking_service_id')
        professional_id = request.session.get('booking_professional_id')
        date_str = request.session.get('booking_date')
        time_str = request.session.get('booking_time')
        client_name = request.session.get('booking_client_name')
        client_email = request.session.get('booking_client_email')
        client_phone = request.session.get('booking_client_phone')
        
        if not all([service_id, professional_id, date_str, time_str, client_name, client_email, client_phone]):
            messages.error(request, "Falha ao processar o agendamento. Dados incompletos.")
            return redirect('booking:start')
            
        # Parse objects
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.datetime.strptime(time_str, '%H:%M').time()
        service = get_object_or_404(Service, id=service_id)
        
        # Use transaction atomic to lock and prevent double-booking
        try:
            with transaction.atomic():
                selected_prof = None
                
                if professional_id != 'none':
                    # Select specific professional
                    prof = Professional.objects.select_for_update().get(id=professional_id)
                    available_slots = get_available_slots(prof, service, date)
                    if time in available_slots:
                        selected_prof = prof
                else:
                    # Select first available professional for "No Preference"
                    _, slots_by_prof = get_available_slots_no_preference(service, date)
                    profs_available = slots_by_prof.get(time, [])
                    if profs_available:
                        # Select first or one with least appts on that day
                        selected_prof = profs_available[0]
                
                if not selected_prof:
                    messages.error(request, "O horário selecionado ficou indisponível. Por favor, selecione outro horário.")
                    return redirect('booking:step2')
                
                # Check double booking check in database directly
                conflict = Appointment.objects.filter(
                    professional=selected_prof,
                    appointment_date=date,
                    appointment_time=time
                ).exclude(status='cancelled').exists()
                
                if conflict:
                    messages.error(request, "O horário selecionado ficou indisponível. Por favor, selecione outro horário.")
                    return redirect('booking:step2')
                
                # Expiration of cancel token: 24h after booking, or 2h before the appt
                # Let's set it as 24h after the appointment time
                appt_datetime = datetime.datetime.combine(date, time)
                appt_tz = timezone.make_aware(appt_datetime, timezone.get_current_timezone())
                cancel_expires = appt_tz + datetime.timedelta(hours=24)
                
                appointment = Appointment.objects.create(
                    professional=selected_prof,
                    service=service,
                    client_name=client_name,
                    client_email=client_email,
                    client_phone=client_phone,
                    appointment_date=date,
                    appointment_time=time,
                    status='confirmed',
                    cancel_token_expires=cancel_expires
                )
                
            # Post-save trigger Celery tasks (or eager sync in development)
            from .tasks import send_confirmation_email, send_professional_notification
            send_confirmation_email.delay(appointment.id)
            send_professional_notification.delay(appointment.id)
            
            # Clear session
            for key in ['booking_service_id', 'booking_professional_id', 'booking_date', 'booking_time', 'booking_client_name', 'booking_client_email', 'booking_client_phone']:
                if key in request.session:
                    del request.session[key]
            
            messages.success(request, "Agendamento realizado com sucesso!")
            return redirect('booking:success', appointment_id=appointment.id)
            
        except Exception as e:
            messages.error(request, f"Erro interno ao salvar agendamento: {str(e)}")
            return redirect('booking:start')


class BookingSuccessView(View):
    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Build google calendar link
        start_dt = datetime.datetime.combine(appointment.appointment_date, appointment.appointment_time)
        end_dt = start_dt + datetime.timedelta(minutes=appointment.service.duration_minutes)
        
        start_str = start_dt.strftime('%Y%m%dT%H%M%S')
        end_str = end_dt.strftime('%Y%m%dT%H%M%S')
        
        title = f"Espaço Delas: {appointment.service.name}"
        details = f"Serviço com {appointment.professional.name}. Duração de {appointment.service.duration_minutes} minutos."
        location = "Espaço Delas Studio, São Paulo"
        
        gcal_base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        gcal_url = f"{gcal_base}&text={urllib.parse.quote(title)}&dates={start_str}/{end_str}&details={urllib.parse.quote(details)}&location={urllib.parse.quote(location)}"
        
        context = {
            'appointment': appointment,
            'gcal_url': gcal_url
        }
        return render(request, 'booking/success.html', context)


class CancelAppointmentView(View):
    def get(self, request, token):
        appointment = get_object_or_404(Appointment, cancel_token=token)
        
        # Check token expiration
        is_expired = False
        if appointment.cancel_token_expires:
            # check if current time is past expiration
            if timezone.now() > appointment.cancel_token_expires:
                is_expired = True
                
        # Also, check if appointment is already cancelled
        is_cancelled = (appointment.status == 'cancelled')
        
        context = {
            'appointment': appointment,
            'is_expired': is_expired,
            'is_cancelled': is_cancelled
        }
        return render(request, 'booking/cancel.html', context)

    def post(self, request, token):
        appointment = get_object_or_404(Appointment, cancel_token=token)
        
        if appointment.cancel_token_expires and timezone.now() > appointment.cancel_token_expires:
            messages.error(request, "O prazo para cancelamento online deste agendamento expirou. Por favor, entre em contato via WhatsApp.")
            return redirect('booking:cancel_view', token=token)
            
        if appointment.status == 'cancelled':
            messages.warning(request, "Este agendamento já foi cancelado.")
            return redirect('booking:cancel_view', token=token)
            
        appointment.status = 'cancelled'
        appointment.save()
        
        # Trigger Celery task
        from .tasks import send_cancellation_email
        send_cancellation_email.delay(appointment.id)
        
        messages.success(request, "Agendamento cancelado com sucesso.")
        return render(request, 'booking/cancel_success.html', {'appointment': appointment})
