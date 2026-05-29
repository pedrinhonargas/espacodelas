import re
from django import forms
from .models import Appointment

class BookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['client_name', 'client_email', 'client_phone']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark placeholder-gray-300 font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'placeholder': 'Digite seu nome completo'
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark placeholder-gray-300 font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'placeholder': 'Digite seu e-mail'
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark placeholder-gray-300 font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'placeholder': '(11) 99999-9999',
                'id': 'phone-input'
            })
        }

    def clean_client_name(self):
        name = self.cleaned_data.get('client_name')
        if not name or len(name.strip()) < 3:
            raise forms.ValidationError("Por favor, digite seu nome completo (mínimo 3 caracteres).")
        return name

    def clean_client_phone(self):
        phone = self.cleaned_data.get('client_phone')
        if not phone:
            raise forms.ValidationError("O telefone é obrigatório.")
        # Clean all non-digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) not in [10, 11]:
            raise forms.ValidationError("Por favor, digite um número de WhatsApp válido com DDD (10 ou 11 dígitos).")
        return phone
