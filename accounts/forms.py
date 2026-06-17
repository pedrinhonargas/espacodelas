from django import forms
from .models import BlockedSlot, Professional
from booking.models import Service

class BlockSlotForm(forms.ModelForm):
    class Meta:
        model = BlockedSlot
        fields = ['block_date', 'start_time', 'end_time', 'reason']
        widgets = {
            'block_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark placeholder-gray-300 font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'placeholder': 'Ex: Consulta médica, Horário de almoço, etc.'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if start and end and start >= end:
            raise forms.ValidationError("O horário de início deve ser anterior ao horário de fim.")
        return cleaned_data


class ProfessionalProfileForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ['name', 'phone', 'google_calendar_email', 'bio', 'photo']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'dash-input'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'dash-input',
                'placeholder': 'Ex: 41988477213'
            }),
            'google_calendar_email': forms.EmailInput(attrs={
                'class': 'dash-input',
                'placeholder': 'profissional@gmail.com'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'dash-input',
                'rows': 4
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full text-sm text-neutral-mid file:mr-4 file:py-2.5 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 cursor-pointer'
            })
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration_minutes', 'price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'rows': 3
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-neutral-dark font-sans text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white transition-all duration-150',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            })
        }
