from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Professional
from .forms import ProfessionalProfileForm

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard:owner')
        elif hasattr(request.user, 'professional_profile'):
            return redirect('dashboard:home')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Bem-vinda, {user.first_name or user.username}!")
                if user.is_staff:
                    return redirect('dashboard:owner')
                elif hasattr(user, 'professional_profile'):
                    return redirect('dashboard:home')
                return redirect('accounts:profile')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.success(request, "Você saiu do sistema.")
    return redirect('core:home')

@login_required
def profile(request):
    try:
        professional = request.user.professional_profile
    except Professional.DoesNotExist:
        messages.error(request, "Você não possui um perfil de profissional associado.")
        return redirect('core:home')
        
    if request.method == 'POST':
        form = ProfessionalProfileForm(request.POST, request.FILES, instance=professional)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('accounts:profile')
    else:
        form = ProfessionalProfileForm(instance=professional)
        
    return render(request, 'dashboard/edit_profile.html', {
        'form': form, 
        'professional': professional,
        'is_profile_page': True
    })
