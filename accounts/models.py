from django.db import models
from django.contrib.auth.models import User

class Professional(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='professional_profile')
    name = models.CharField('Nome', max_length=100)
    role = models.CharField('Especialidade', max_length=100, help_text="Ex: Manicure, Designer de Sobrancelhas")
    bio = models.TextField('Biografia', blank=True)
    photo = models.ImageField('Foto', upload_to='professionals/', blank=True, null=True)
    phone = models.CharField('WhatsApp/Telefone', max_length=20, blank=True, help_text="Apenas números com DDD, ex: 41988477213")
    google_calendar_email = models.EmailField('Gmail (Google Agenda)', blank=True, help_text="E-mail Gmail da profissional para receber convites de agendamento na agenda do Google")
    is_active = models.BooleanField('Ativo', default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def first_name(self):
        return self.name.split()[0] if self.name else ""

    @property
    def formatted_phone(self):
        if not self.phone or len(self.phone) < 10:
            return self.phone
        p = self.phone
        return f"({p[:2]}) {p[2:7]}-{p[7:]}"

class WorkingHours(models.Model):
    WEEKDAYS = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='working_hours')
    weekday = models.IntegerField('Dia da Semana', choices=WEEKDAYS, db_index=True)
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Fim')
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Horário de Trabalho'
        verbose_name_plural = 'Horários de Trabalho'
        unique_together = ('professional', 'weekday')
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.professional.name} - {self.get_weekday_display()}: {self.start_time.strftime('%H:%M')} às {self.end_time.strftime('%H:%M')}"

class BlockedSlot(models.Model):
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='blocked_slots')
    block_date = models.DateField('Data do Bloqueio', db_index=True)
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Fim')
    reason = models.CharField('Motivo', max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Horário Bloqueado'
        verbose_name_plural = 'Horários Bloqueados'
        ordering = ['block_date', 'start_time']

    def __str__(self):
        return f"{self.professional.name} - Bloqueio em {self.block_date.strftime('%d/%m/%Y')} das {self.start_time.strftime('%H:%M')} às {self.end_time.strftime('%H:%M')}"
