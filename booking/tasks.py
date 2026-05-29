from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Appointment, EmailLog

def send_html_email(subject, template_name, context, to_email, email_type, appointment):
    """
    Helper function to send HTML email and log the result in EmailLog.
    """
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'no-reply@espacodelas.com.br',
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Log success
        EmailLog.objects.create(
            appointment=appointment,
            email_type=email_type,
            recipient_email=to_email,
            sent_success=True
        )
        return True
    except Exception as e:
        print(f"Error sending email of type {email_type} to {to_email}: {str(e)}")
        # Log failure
        EmailLog.objects.create(
            appointment=appointment,
            email_type=email_type,
            recipient_email=to_email,
            sent_success=False
        )
        return False

@shared_task
def send_confirmation_email(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return False
        
    context = {
        'appointment': appointment,
        'cancel_url': f"/agendar/cancelar/{appointment.cancel_token}/"
    }
    
    return send_html_email(
        subject="Confirmação de Agendamento - Espaço Delas",
        template_name="emails/confirmation.html",
        context=context,
        to_email=appointment.client_email,
        email_type="confirmation",
        appointment=appointment
    )

@shared_task
def send_professional_notification(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return False
        
    context = {
        'appointment': appointment
    }
    
    # Send to the professional's user email if available, otherwise fallback
    to_email = appointment.professional.user.email if appointment.professional.user else "contato@espacodelas.com.br"
    
    return send_html_email(
        subject=f"Novo Agendamento: {appointment.client_name} - {appointment.service.name}",
        template_name="emails/professional_notification.html",
        context=context,
        to_email=to_email,
        email_type="confirmation",
        appointment=appointment
    )

@shared_task
def send_cancellation_email(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return False
        
    context = {
        'appointment': appointment
    }
    
    # Notify client
    client_sent = send_html_email(
        subject="Cancelamento de Agendamento - Espaço Delas",
        template_name="emails/cancellation.html",
        context=context,
        to_email=appointment.client_email,
        email_type="cancellation",
        appointment=appointment
    )
    
    # Notify professional
    prof_email = appointment.professional.user.email if appointment.professional.user else "contato@espacodelas.com.br"
    prof_sent = send_html_email(
        subject=f"Agendamento Cancelado: {appointment.client_name} - {appointment.service.name}",
        template_name="emails/cancellation_professional.html",
        context=context,
        to_email=prof_email,
        email_type="cancellation",
        appointment=appointment
    )
    
    return client_sent and prof_sent

@shared_task
def send_reminder_email(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return False
        
    context = {
        'appointment': appointment,
        'cancel_url': f"/agendar/cancelar/{appointment.cancel_token}/"
    }
    
    return send_html_email(
        subject="Lembrete de Agendamento amanhã - Espaço Delas",
        template_name="emails/reminder.html",
        context=context,
        to_email=appointment.client_email,
        email_type="reminder_24h",
        appointment=appointment
    )

@shared_task
def schedule_reminders():
    import datetime
    from django.utils import timezone
    
    today = timezone.localtime(timezone.now()).date()
    tomorrow = today + datetime.timedelta(days=1)
    
    # Get confirmed appointments for tomorrow
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status='confirmed'
    )
    
    sent_count = 0
    for app in appointments:
        # Check if already sent
        already_sent = EmailLog.objects.filter(
            appointment=app,
            email_type='reminder_24h',
            sent_success=True
        ).exists()
        
        if not already_sent:
            send_reminder_email.delay(app.id)
            sent_count += 1
            
    return f"Scheduled {sent_count} reminders for {tomorrow}."

