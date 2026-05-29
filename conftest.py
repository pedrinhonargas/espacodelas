"""
Conftest — shared fixtures for all apps.
"""
import datetime
import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import Professional, WorkingHours, BlockedSlot
from booking.models import Service, ProfessionalService, Appointment


# ── User / Professional factories ────────────────────────────

@pytest.fixture
def create_user(db):
    """Factory fixture for creating Django users."""
    def _create(username="testuser", email="test@example.com", password="senha123", is_staff=False, **kw):
        return User.objects.create_user(
            username=username, email=email, password=password, is_staff=is_staff, **kw
        )
    return _create


@pytest.fixture
def create_professional(db, create_user):
    """Factory fixture for creating Professional + linked User."""
    _counter = [0]

    def _create(name="Alessandra", role="Manicure", is_active=True, user=None, **kw):
        _counter[0] += 1
        if user is None:
            user = create_user(
                username=f"prof_{_counter[0]}",
                email=f"prof{_counter[0]}@espacodelas.com.br"
            )
        return Professional.objects.create(
            user=user, name=name, role=role, is_active=is_active, **kw
        )
    return _create


@pytest.fixture
def create_service(db):
    """Factory fixture for creating a Service."""
    _counter = [0]

    def _create(name="Manicure Clássica", duration_minutes=30, price=40.00, is_active=True, **kw):
        _counter[0] += 1
        return Service.objects.create(
            name=f"{name} {_counter[0]}" if _counter[0] > 1 else name,
            duration_minutes=duration_minutes,
            price=price,
            is_active=is_active,
            **kw
        )
    return _create


@pytest.fixture
def create_working_hours(db):
    """Factory fixture for WorkingHours."""
    def _create(professional, weekday=0, start_time=datetime.time(9, 0), end_time=datetime.time(19, 0), is_active=True):
        return WorkingHours.objects.create(
            professional=professional,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active
        )
    return _create


@pytest.fixture
def create_blocked_slot(db):
    """Factory fixture for BlockedSlot."""
    def _create(professional, block_date=None, start_time=datetime.time(12, 0), end_time=datetime.time(13, 0), reason="Almoço"):
        if block_date is None:
            block_date = timezone.localtime(timezone.now()).date() + datetime.timedelta(days=1)
        return BlockedSlot.objects.create(
            professional=professional,
            block_date=block_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason
        )
    return _create


@pytest.fixture
def create_appointment(db):
    """Factory fixture for Appointment."""
    def _create(professional, service, date=None, time=datetime.time(10, 0), status='confirmed', **kw):
        if date is None:
            date = timezone.localtime(timezone.now()).date() + datetime.timedelta(days=1)
        return Appointment.objects.create(
            professional=professional,
            service=service,
            client_name=kw.get('client_name', 'Maria da Silva'),
            client_email=kw.get('client_email', 'maria@email.com'),
            client_phone=kw.get('client_phone', '11999998888'),
            appointment_date=date,
            appointment_time=time,
            status=status,
            cancel_token_expires=timezone.now() + datetime.timedelta(hours=72),
        )
    return _create


@pytest.fixture
def link_service(db):
    """Links a professional to a service via ProfessionalService."""
    def _link(professional, service):
        return ProfessionalService.objects.create(professional=professional, service=service)
    return _link


# ── Convenience combo fixture ────────────────────────────────

@pytest.fixture
def setup_booking_scenario(create_professional, create_service, create_working_hours, link_service):
    """
    Sets up a typical booking scenario:
    - 1 professional (Alessandra, Manicure)
    - 1 service (Manicure Clássica, 30 min, R$ 40)
    - Working hours Mon-Sat 9-19
    - Professional linked to the service
    Returns (professional, service).
    """
    prof = create_professional(name="Alessandra", role="Manicure")
    service = create_service(name="Manicure Clássica", duration_minutes=30, price=40.00)
    link_service(prof, service)
    for day in range(6):  # Mon-Sat
        create_working_hours(prof, weekday=day)
    return prof, service
