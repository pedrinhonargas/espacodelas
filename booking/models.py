import uuid
from django.db import models
from accounts.models import Professional

class Service(models.Model):
    name = models.CharField('Nome do Serviço', max_length=100)
    description = models.TextField('Descrição', blank=True)
    duration_minutes = models.PositiveIntegerField('Duração (minutos)', default=30)
    price = models.DecimalField('Preço (R$)', max_length=10, max_digits=8, decimal_places=2)
    is_active = models.BooleanField('Ativo', default=True)
    professionals = models.ManyToManyField(Professional, through='ProfessionalService', related_name='services')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min - R$ {self.price})"

class ProfessionalService(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Serviço por Profissional'
        verbose_name_plural = 'Serviços por Profissional'
        unique_together = ('professional', 'service')

    def __str__(self):
        return f"{self.professional.name} - {self.service.name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
    ]

    professional = models.ForeignKey(Professional, on_delete=models.PROTECT, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='appointments')
    client_name = models.CharField('Nome da Cliente', max_length=100)
    client_email = models.EmailField('E-mail da Cliente')
    client_phone = models.CharField('WhatsApp da Cliente', max_length=20)
    appointment_date = models.DateField('Data do Agendamento', db_index=True)
    appointment_time = models.TimeField('Horário do Agendamento')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='confirmed', db_index=True) # default confirmed as per standard direct booking or pending
    cancel_token = models.UUIDField('Token de Cancelamento', default=uuid.uuid4, unique=True, editable=False)
    cancel_token_expires = models.DateTimeField('Expiração do Token', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"{self.client_name} - {self.service.name} com {self.professional.name} ({self.appointment_date.strftime('%d/%m/%Y')} às {self.appointment_time.strftime('%H:%M')})"

class EmailLog(models.Model):
    EMAIL_TYPES = [
        ('confirmation', 'Confirmação'),
        ('reminder_24h', 'Lembrete 24h'),
        ('cancellation', 'Cancelamento'),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField('Tipo de E-mail', max_length=20, choices=EMAIL_TYPES)
    recipient_email = models.EmailField('Destinatário')
    sent_success = models.BooleanField('Enviado com Sucesso', default=True)
    sent_at = models.DateTimeField('Enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Log de E-mail'
        verbose_name_plural = 'Logs de E-mail'
        ordering = ['-sent_at']

    def __str__(self):
        status = 'Sucesso' if self.sent_success else 'Falha'
        return f"E-mail {self.get_email_type_display()} para {self.recipient_email} - {status}"
