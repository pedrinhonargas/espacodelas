from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.BookingStep1View.as_view(), name='start'),
    path('data-hora/', views.BookingStep2View.as_view(), name='step2'),
    path('dados/', views.BookingStep3View.as_view(), name='step3'),
    path('confirmar/', views.BookingConfirmView.as_view(), name='confirm'),
    path('sucesso/<int:appointment_id>/', views.BookingSuccessView.as_view(), name='success'),
    path('cancelar/<uuid:token>/', views.CancelAppointmentView.as_view(), name='cancel_view'),
    path('horarios/ajax/', views.BookingSlotsAjaxView.as_view(), name='slots_ajax'),
]
