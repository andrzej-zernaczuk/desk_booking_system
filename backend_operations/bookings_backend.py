import logging
from typing import Callable, Any
from datetime import datetime
from sqlalchemy.sql import select
from sqlalchemy.orm import Session

from db.db_models import Desk, Booking, Status
from db.session_management import managed_session
from backend_operations.log_utils import log_event
from backend_operations.user_login import get_current_user


def create_booking(
        event: Any,
        session_factory: Callable[[], Session],
        desk_code: str,
        selected_date: str,
        start_time: str,
        end_time: str
    ):
    """Create Booking for logged in user.

    :param session_factory: A callable that returns a SQLAlchemy session
    :param desk_code: The code of the desk to be booked
    :param selected_date: The selected booking date
    :param start_time: The start time of the booking
    :param end_time: The end time of the booking
    """
    try:
        # Convert start_time and end_time to datetime objects
        start_time_dt = datetime.strptime(f"{selected_date} {start_time}", "%Y-%m-%d %H:%M")
        end_time_dt = datetime.strptime(f"{selected_date} {end_time}", "%Y-%m-%d %H:%M")

        # Check if start_time is before end_time
        if start_time_dt >= end_time_dt:
            raise ValueError("End time must be after start time.")

        with managed_session(session_factory) as session:
            # Ensure the user is logged in
            current_user: str = get_current_user()

            if not current_user:
                raise ValueError("No user is currently logged in.")

            # Check if the desk exists
            desk_exists = session.execute(
                select(Desk).where(Desk.desk_code == desk_code)
            ).scalar_one_or_none()

            if not desk_exists:
                raise ValueError(f"Desk '{desk_code}' does not exist.")

            # Get pending status id
            pending_status = session.execute(
                select(Status.status_id).where(Status.status_name == "Pending")
            ).scalar_one_or_none()

            if not pending_status:
                raise ValueError("The 'Pending' status does not exist in the database.")

            # Check for overlapping bookings
            overlapping_bookings = session.execute(
                select(Booking).where(
                    Booking.desk_code == desk_code,
                    Booking.start_date < end_time_dt,
                    Booking.end_date > start_time_dt
                )
            ).scalars().all()

            if overlapping_bookings:
                raise ValueError(f"The desk '{desk_code}' is already booked for the selected time range.")

            # Create the booking
            new_booking = Booking(
                user_name=current_user,
                desk_code=desk_code,
                start_date=start_time_dt,
                end_date=end_time_dt,
                status_id=pending_status
            )

            session.add(new_booking)
            session.commit()

            # Log the successful booking creation
            logging.info(f"Booking created successfully for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}' by user '{current_user}'.")
            log_event(
                current_user,
                "Success",
                "Booking",
                f"Booking created successfully for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}'"
            )

    except ValueError as val_err:
        # Handle user-input errors (e.g., invalid desk or time range)
        logging.error(f"Error while creating booking for '{desk_code}' with start time: '{start_time}' and end time: '{end_time}' for user: '{get_current_user()}': {val_err}")
        log_event(get_current_user(), "Failure", "Booking", f"Booking creation failed for '{desk_code}' with start time: '{start_time}' and end time: '{end_time}': {val_err}")
        raise

    except Exception as exc:
        logging.error(f"Error while creating booking for '{desk_code}' with start time: '{start_time}' and end time: '{end_time}' for user: '{get_current_user()}': {exc}")
        log_event(get_current_user(), "Failure", "Booking", f"Booking creation failed for '{desk_code}' with start time: '{start_time}' and end time: '{end_time}': {exc}")
        raise
