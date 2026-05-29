"""
Tests for booking views — booking flow, cancellation, and AJAX.
"""
import datetime
import uuid
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from booking.models import Appointment


class TestBookingFlowViews:
    """Test the multi-step booking flow."""

    def test_step1_get(self, setup_booking_scenario, client):
        """GET /agendar/ should render step1 with services and professionals."""
        url = reverse('booking:start')
        response = client.get(url)
        assert response.status_code == 200
        assert b'Manicure' in response.content or b'servico' in response.content.lower() or b'Servi' in response.content

    def test_step1_post_redirects_to_step2(self, setup_booking_scenario, client):
        """POST /agendar/ with a service should redirect to step2."""
        prof, service = setup_booking_scenario
        url = reverse('booking:start')
        response = client.post(url, {'service': service.id, 'professional': prof.id})
        assert response.status_code == 302
        assert 'data-hora' in response.url

    def test_step1_post_without_service_redirects_with_error(self, setup_booking_scenario, client):
        """POST /agendar/ without a service should redirect back."""
        url = reverse('booking:start')
        response = client.post(url, {})
        assert response.status_code == 302

    def test_step2_requires_session(self, client, setup_booking_scenario):
        """GET /agendar/data-hora/ without session data should redirect."""
        url = reverse('booking:step2')
        response = client.get(url)
        assert response.status_code == 302

    def test_step3_requires_session(self, client, setup_booking_scenario):
        """GET /agendar/dados/ without session data should redirect."""
        url = reverse('booking:step3')
        response = client.get(url)
        assert response.status_code == 302

    def test_confirm_requires_session(self, client, setup_booking_scenario):
        """GET /agendar/confirmar/ without session data should redirect."""
        url = reverse('booking:confirm')
        response = client.get(url)
        assert response.status_code == 302

    def test_full_booking_flow_creates_appointment(self, setup_booking_scenario, client):
        """Full booking flow with valid data should create an Appointment."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        # Step 1: select service & professional
        session = client.session
        session['booking_service_id'] = str(service.id)
        session['booking_professional_id'] = str(prof.id)
        session['booking_date'] = next_monday.strftime('%Y-%m-%d')
        session['booking_time'] = '10:00'
        session['booking_client_name'] = 'Teste Cliente'
        session['booking_client_email'] = 'teste@email.com'
        session['booking_client_phone'] = '11999998888'
        session.save()

        # Confirm
        url = reverse('booking:confirm')
        response = client.post(url)
        assert response.status_code == 302  # redirect to success

        # Verify appointment was created
        appt = Appointment.objects.filter(
            professional=prof,
            service=service,
            appointment_date=next_monday,
            appointment_time=datetime.time(10, 0)
        ).first()
        assert appt is not None
        assert appt.status == 'confirmed'
        assert appt.client_name == 'Teste Cliente'

    def test_booking_occupied_slot_returns_error(self, setup_booking_scenario, create_appointment, client):
        """Booking an already occupied slot should not create a double booking."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        # Pre-book the slot
        create_appointment(prof, service, date=next_monday, time=datetime.time(10, 0))

        # Try to book same slot
        session = client.session
        session['booking_service_id'] = str(service.id)
        session['booking_professional_id'] = str(prof.id)
        session['booking_date'] = next_monday.strftime('%Y-%m-%d')
        session['booking_time'] = '10:00'
        session['booking_client_name'] = 'Outra Cliente'
        session['booking_client_email'] = 'outra@email.com'
        session['booking_client_phone'] = '11888887777'
        session.save()

        url = reverse('booking:confirm')
        response = client.post(url)
        # Should redirect (either to step2 with error or to start)
        assert response.status_code == 302

        # Should NOT have created a second appointment at that slot
        count = Appointment.objects.filter(
            professional=prof,
            appointment_date=next_monday,
            appointment_time=datetime.time(10, 0)
        ).exclude(status='cancelled').count()
        assert count == 1


class TestBookingSuccessView:
    """Tests for the success page."""

    def test_success_page_shows_appointment(self, setup_booking_scenario, create_appointment, client):
        """GET /agendar/sucesso/<id>/ should display appointment details."""
        prof, service = setup_booking_scenario
        appt = create_appointment(prof, service)
        url = reverse('booking:success', kwargs={'appointment_id': appt.id})
        response = client.get(url)
        assert response.status_code == 200
        assert appt.client_email.encode() in response.content

    def test_success_page_404_for_invalid_id(self, client, setup_booking_scenario):
        """GET /agendar/sucesso/99999/ should return 404."""
        url = reverse('booking:success', kwargs={'appointment_id': 99999})
        response = client.get(url)
        assert response.status_code == 404


class TestCancelAppointmentView:
    """Tests for the cancellation flow via token."""

    def test_cancel_page_shows_appointment_details(self, setup_booking_scenario, create_appointment, client):
        """GET /agendar/cancelar/<token>/ should show appointment."""
        prof, service = setup_booking_scenario
        appt = create_appointment(prof, service)
        url = reverse('booking:cancel_view', kwargs={'token': str(appt.cancel_token)})
        response = client.get(url)
        assert response.status_code == 200
        assert appt.client_name.encode() in response.content

    def test_cancel_post_cancels_appointment(self, setup_booking_scenario, create_appointment, client):
        """POST /agendar/cancelar/<token>/ should cancel the appointment."""
        prof, service = setup_booking_scenario
        appt = create_appointment(prof, service)
        url = reverse('booking:cancel_view', kwargs={'token': str(appt.cancel_token)})
        response = client.post(url)
        assert response.status_code == 200  # renders cancel_success template

        appt.refresh_from_db()
        assert appt.status == 'cancelled'

    def test_cancel_invalid_token_returns_404(self, client, setup_booking_scenario):
        """POST with a non-existent token should return 404."""
        fake_token = uuid.uuid4()
        url = reverse('booking:cancel_view', kwargs={'token': str(fake_token)})
        response = client.get(url)
        assert response.status_code == 404

    def test_cancel_expired_token_shows_warning(self, setup_booking_scenario, create_appointment, client):
        """POST with expired token should not cancel."""
        prof, service = setup_booking_scenario
        appt = create_appointment(prof, service)
        # Force expire the token
        appt.cancel_token_expires = timezone.now() - datetime.timedelta(hours=1)
        appt.save()

        url = reverse('booking:cancel_view', kwargs={'token': str(appt.cancel_token)})
        response = client.post(url)
        assert response.status_code == 302  # redirect back with error

        appt.refresh_from_db()
        assert appt.status == 'confirmed'  # should NOT be cancelled

    def test_cancel_already_cancelled_appointment(self, setup_booking_scenario, create_appointment, client):
        """Cancelling an already-cancelled appointment shows warning."""
        prof, service = setup_booking_scenario
        appt = create_appointment(prof, service, status='cancelled')
        url = reverse('booking:cancel_view', kwargs={'token': str(appt.cancel_token)})
        response = client.post(url)
        assert response.status_code == 302  # redirect with warning


class TestBookingSlotsAjaxView:
    """Tests for the AJAX slots endpoint."""

    def test_ajax_returns_slots(self, setup_booking_scenario, client):
        """GET /agendar/horarios/ajax/?data=...&servico_id=...&profissional_id=... should return JSON."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        # Set session data as the view checks session first
        session = client.session
        session['booking_service_id'] = str(service.id)
        session['booking_professional_id'] = str(prof.id)
        session.save()

        url = reverse('booking:slots_ajax')
        response = client.get(url, {
            'data': next_monday.strftime('%Y-%m-%d'),
            'servico_id': service.id,
            'profissional_id': prof.id,
        })
        assert response.status_code == 200
        data = response.json()
        assert 'slots' in data
        assert isinstance(data['slots'], list)

    def test_ajax_missing_params_returns_400(self, client, setup_booking_scenario):
        """AJAX without required params should return 400."""
        url = reverse('booking:slots_ajax')
        response = client.get(url)
        assert response.status_code == 400
