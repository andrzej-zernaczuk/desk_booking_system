import pytz
from datetime import datetime


def get_time_change():
    try:
        # Define the Poland timezone
        poland_tz = pytz.timezone("Europe/Warsaw")

        # Get the current time in UTC and convert it to Poland timezone
        now_utc = datetime.now(pytz.utc)  # Get current time in UTC with timezone info
        now_poland = now_utc.astimezone(poland_tz)  # Convert to Poland timezone

        # Calculate the time offset in hours from UTC
        offset = now_poland.utcoffset()
        if offset is not None:
            return int(offset.total_seconds() / 3600)  # Return the offset in hours
        else:
            raise ValueError("Could not calculate UTC offset for Europe/Warsaw.")
    except Exception as e:
        raise ValueError(f"Error in get_time_change: {e}")
