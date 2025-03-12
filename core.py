from calendar import monthrange
from datetime import datetime
from typing import Optional


# Simple helper to provide the current POSIX timestamp.
class PosixTime:
    @staticmethod
    def now() -> int:
        return int(datetime.utcnow().timestamp())

def seconds_to_text(
    seconds: int,
    output_format: int = 0,
    from_timestamp: Optional[int] = None
) -> Optional[str]:
    """
    Format seconds into a human-readable duration string with configurable precision.

    Args:
        seconds: Number of seconds (positive or negative)
        output_format: Controls output format:
            0 = full precision (years, months, days, hours, minutes, seconds)
            1 = up to days
            2 = up to months (with rounding)
            3 = only years (with rounding)
            -1 = total months and remaining days + time
            -2 = total days + time
            -3 = total hours + minutes and seconds

    Returns:
        Formatted string with appropriate units or None if seconds is 0.
    """
    if seconds == 0:
        return None

    now_stamp = from_timestamp or PosixTime.now()
    # Duration is interpreted as the difference between now and the provided seconds.
    duration = now_stamp - seconds

    sign = "-" if seconds < 0 else ""
    abs_seconds = abs(seconds)

    def get_days_in_range(years: int, months: int) -> int:
        total_days = 0
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        current_date = start_date
        for _ in range(years * 12 + months):
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            total_days += days_in_month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        return total_days

    minutes, secs = divmod(abs_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    # Approximate months and years using average days per month (30.44)
    months = int(days / 30.44)
    years, months = divmod(months, 12)

    # Adjust days based on actual calendar months.
    remaining_days = days - get_days_in_range(years, months)

    if output_format == -3:
        total_hours = (days * 24) + hours
        return f"{sign}{total_hours}:{minutes:02d}:{secs:02d}"

    if output_format == -2:
        return f"{sign}{days} days, {hours:02d}h{minutes:02d}m{secs:02d}s"

    if output_format == -1:
        total_months = (years * 12) + months
        return f"{sign}{total_months} months, {remaining_days} days, {hours:02d}h{minutes:02d}m{secs:02d}s"

    if output_format == 2 and remaining_days > 15:
        months += 1
        if months == 12:
            years += 1
            months = 0

    parts = []
    if years > 0:
        parts.append(f"{years} years")
    if output_format <= 2 and months > 0:
        parts.append(f"{months} months")
    if output_format <= 1 and remaining_days > 0:
        parts.append(f"{remaining_days} days")
    if output_format <= 0:
        if hours > 0 or minutes > 0 or secs > 0:
            parts.append(f"{hours:02d}h{minutes:02d}m{secs:02d}s")
    if not parts:
        return "0"
    return sign + ", ".join(parts)

def format_timestamp(ts: int) -> str:
    try:
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Invalid timestamp"