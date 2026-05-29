import datetime
from django.utils import timezone
from accounts.models import WorkingHours, BlockedSlot, Professional
from booking.models import Appointment

def time_to_minutes(t):
    return t.hour * 60 + t.minute

def minutes_to_time(m):
    return datetime.time(m // 60, m % 60)

def get_available_slots(professional, service, date):
    """
    Returns a list of datetime.time objects indicating the start times of available slots
    for a specific professional, service, and date.
    """
    if not professional.is_active:
        return []

    # Get weekday (0=Segunda, 5=Sábado, 6=Domingo)
    weekday = date.weekday()
    
    # Get working hours
    try:
        working_hours = WorkingHours.objects.get(professional=professional, weekday=weekday, is_active=True)
    except WorkingHours.DoesNotExist:
        return []

    start_min = time_to_minutes(working_hours.start_time)
    end_min = time_to_minutes(working_hours.end_time)
    duration = service.duration_minutes

    # Get blocked slots
    blocked_slots = BlockedSlot.objects.filter(professional=professional, block_date=date)
    blocked_intervals = [
        (time_to_minutes(b.start_time), time_to_minutes(b.end_time))
        for b in blocked_slots
    ]

    # Get active appointments
    appointments = Appointment.objects.filter(
        professional=professional,
        appointment_date=date
    ).exclude(status='cancelled')
    
    app_intervals = [
        (time_to_minutes(app.appointment_time), time_to_minutes(app.appointment_time) + app.service.duration_minutes)
        for app in appointments
    ]

    # Generate slots
    candidate_start = start_min
    slots = []

    now = timezone.localtime(timezone.now())
    is_today = (date == now.date())
    current_time_min = now.hour * 60 + now.minute

    while candidate_start + duration <= end_min:
        candidate_end = candidate_start + duration

        # If booking for today, exclude past times (add a 30-min buffer)
        if is_today and candidate_start <= current_time_min + 30:
            candidate_start += 30
            continue

        # Check overlap
        overlapped = False
        
        # Blocked slot overlap
        for b_start, b_end in blocked_intervals:
            if max(candidate_start, b_start) < min(candidate_end, b_end):
                overlapped = True
                break

        # Appointment overlap
        if not overlapped:
            for a_start, a_end in app_intervals:
                if max(candidate_start, a_start) < min(candidate_end, a_end):
                    overlapped = True
                    break

        if not overlapped:
            slots.append(minutes_to_time(candidate_start))

        candidate_start += 30

    return slots

def get_available_slots_no_preference(service, date):
    """
    Returns a sorted list of unique start times where at least one professional is available,
    along with a dictionary mapping time -> list of available professionals.
    """
    professionals = Professional.objects.filter(is_active=True, services=service)
    slots_by_time = {}
    
    for prof in professionals:
        slots = get_available_slots(prof, service, date)
        for s in slots:
            if s not in slots_by_time:
                slots_by_time[s] = []
            slots_by_time[s].append(prof)
            
    sorted_times = sorted(list(slots_by_time.keys()))
    return sorted_times, slots_by_time

def get_available_dates(service, professional=None, months_ahead=2):
    """
    Returns a set of date strings (YYYY-MM-DD) that have at least one available slot.
    Generates availability starting from today up to months_ahead.
    """
    today = timezone.localtime(timezone.now()).date()
    end_date = today + datetime.timedelta(days=30 * months_ahead)
    
    available_dates = []
    current = today
    
    while current <= end_date:
        if professional:
            slots = get_available_slots(professional, service, current)
        else:
            slots, _ = get_available_slots_no_preference(service, current)
            
        if slots:
            available_dates.append(current.strftime('%Y-%m-%d'))
            
        current += datetime.timedelta(days=1)
        
    return available_dates
