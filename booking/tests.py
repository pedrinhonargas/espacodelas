"""
Tests for booking/utils.py — slot availability logic.
"""
import datetime
import pytest
from unittest.mock import patch
from django.utils import timezone

from booking.utils import get_available_slots, get_available_slots_no_preference, get_available_dates


class TestGetAvailableSlots:
    """Tests for get_available_slots()."""

    def test_returns_slots_for_valid_working_day(self, setup_booking_scenario):
        """Professional with working hours should have slots on a valid weekday."""
        prof, service = setup_booking_scenario
        # Pick a future Monday
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7  # next monday
        next_monday = today + datetime.timedelta(days=days_until_monday)

        slots = get_available_slots(prof, service, next_monday)
        assert len(slots) > 0
        # Slots should be sorted
        assert slots == sorted(slots)
        # All slots should be within 09:00-19:00
        for s in slots:
            assert s >= datetime.time(9, 0)
            assert s <= datetime.time(18, 30)  # 18:30 + 30min = 19:00

    def test_no_slots_on_sunday(self, setup_booking_scenario):
        """Sunday (weekday=6) has no working hours configured → no slots."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_sunday = (6 - today.weekday()) % 7 or 7
        next_sunday = today + datetime.timedelta(days=days_until_sunday)

        slots = get_available_slots(prof, service, next_sunday)
        assert slots == []

    def test_no_slots_for_inactive_professional(self, create_professional, create_service, create_working_hours, link_service):
        """Inactive professional should return no slots."""
        prof = create_professional(name="Inativa", is_active=False)
        service = create_service()
        link_service(prof, service)
        create_working_hours(prof, weekday=0)

        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        slots = get_available_slots(prof, service, next_monday)
        assert slots == []

    def test_blocked_slot_removes_availability(self, setup_booking_scenario, create_blocked_slot):
        """A blocked slot should remove those times from availability."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        # Block 10:00-11:00
        create_blocked_slot(
            prof,
            block_date=next_monday,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0)
        )

        slots = get_available_slots(prof, service, next_monday)
        # 10:00 and 10:30 should NOT be in slots (30 min service overlaps blocked range)
        assert datetime.time(10, 0) not in slots
        assert datetime.time(10, 30) not in slots
        # 09:00 and 11:00 should still be available
        assert datetime.time(9, 0) in slots or datetime.time(9, 30) in slots
        assert datetime.time(11, 0) in slots

    def test_existing_appointment_removes_slot(self, setup_booking_scenario, create_appointment):
        """An existing confirmed appointment should block its time slot."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        create_appointment(prof, service, date=next_monday, time=datetime.time(14, 0))

        slots = get_available_slots(prof, service, next_monday)
        assert datetime.time(14, 0) not in slots

    def test_cancelled_appointment_does_not_block_slot(self, setup_booking_scenario, create_appointment):
        """A cancelled appointment should NOT block the slot."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        create_appointment(prof, service, date=next_monday, time=datetime.time(14, 0), status='cancelled')

        slots = get_available_slots(prof, service, next_monday)
        assert datetime.time(14, 0) in slots

    def test_all_slots_occupied(self, setup_booking_scenario, create_appointment):
        """When all slots are occupied, should return empty list."""
        prof, service = setup_booking_scenario
        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        # Book every 30 min slot from 9:00 to 18:30
        t = datetime.time(9, 0)
        while t < datetime.time(19, 0):
            create_appointment(prof, service, date=next_monday, time=t,
                               client_name=f"Cliente {t.strftime('%H%M')}",
                               client_email=f"c{t.strftime('%H%M')}@x.com")
            minutes = t.hour * 60 + t.minute + 30
            if minutes >= 19 * 60:
                break
            t = datetime.time(minutes // 60, minutes % 60)

        slots = get_available_slots(prof, service, next_monday)
        assert slots == []


class TestGetAvailableSlotsNoPreference:
    """Tests for get_available_slots_no_preference()."""

    def test_merges_slots_from_multiple_professionals(
        self, create_professional, create_service, create_working_hours, link_service
    ):
        """Should return unified slots from all active professionals offering the service."""
        service = create_service(name="Manicure Gel")
        prof1 = create_professional(name="Alessandra")
        prof2 = create_professional(name="Luana")
        link_service(prof1, service)
        link_service(prof2, service)

        today = timezone.localtime(timezone.now()).date()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + datetime.timedelta(days=days_until_monday)

        create_working_hours(prof1, weekday=next_monday.weekday())
        create_working_hours(prof2, weekday=next_monday.weekday())

        sorted_times, slots_by_time = get_available_slots_no_preference(service, next_monday)
        assert len(sorted_times) > 0
        # Each time should have at least one professional
        for t in sorted_times:
            assert len(slots_by_time[t]) >= 1


class TestGetAvailableDates:
    """Tests for get_available_dates()."""

    def test_returns_future_dates_with_availability(self, setup_booking_scenario):
        """Should return a list of date strings."""
        prof, service = setup_booking_scenario
        dates = get_available_dates(service, professional=prof, months_ahead=1)
        assert isinstance(dates, list)
        assert len(dates) > 0
        # All dates should be YYYY-MM-DD format
        for d in dates:
            datetime.datetime.strptime(d, '%Y-%m-%d')

    def test_no_dates_for_inactive_professional(self, create_professional, create_service, link_service):
        """Inactive professional → no available dates."""
        prof = create_professional(name="Inativa", is_active=False)
        service = create_service()
        link_service(prof, service)
        dates = get_available_dates(service, professional=prof, months_ahead=1)
        assert dates == []
