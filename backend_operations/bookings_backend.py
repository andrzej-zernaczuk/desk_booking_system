import logging
import sqlalchemy
from typing import Callable
from datetime import datetime
from sqlalchemy.sql import select, desc, func
from sqlalchemy.orm import Session
from tkinter import messagebox, Event

from db.db_models import Booking, Office, Floor, Desk, Status, MostFrequentUser
from db.session_management import managed_session
from backend_operations.log_utils import log_event
from backend_operations.user_login import get_current_user


def create_booking(
    event: Event,
    session_factory: Callable[[], Session],
    desk_code: str,
    selected_date: str,
    start_time: str,
    end_time: str,
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
            desk_exists = session.execute(select(Desk).where(Desk.desk_code == desk_code)).scalar_one_or_none()

            if not desk_exists:
                raise ValueError(f"Desk '{desk_code}' does not exist.")

            # Get pending status id
            pending_status = session.execute(
                select(Status.status_id).where(Status.status_name == "Pending")
            ).scalar_one_or_none()

            canceled_status = session.execute(
                select(Status).where(Status.status_name == "Canceled")
            ).scalar_one_or_none()

            if not pending_status or not canceled_status:
                raise ValueError("The 'Pending' status does not exist in the database.")

            # Check for overlapping bookings
            overlapping_bookings = (
                session.execute(
                    select(Booking).where(
                        Booking.desk_code == desk_code,
                        Booking.start_date < end_time_dt,
                        Booking.end_date > start_time_dt,
                        Booking.status_id != canceled_status.status_id,
                    )
                )
                .scalars()
                .all()
            )

            if overlapping_bookings:
                raise ValueError(f"The desk '{desk_code}' is already booked for the selected time range.")

            # Create the booking
            new_booking = Booking(
                user_name=current_user,
                desk_code=desk_code,
                start_date=start_time_dt,
                end_date=end_time_dt,
                status_id=pending_status,
            )

            session.add(new_booking)
            session.commit()

            # Log the successful booking creation
            logging.info(
                f"Booking created successfully for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}' by user '{current_user}'."
            )
            log_event(
                current_user,
                "Success",
                "Booking",
                f"Booking created successfully for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}'",
            )
            # Notify the user of success
            messagebox.showinfo(
                title="Booking Successful",
                message=f"Booking created successfully for desk '{desk_code}' from {start_time} to {end_time}.",
            )

    except sqlalchemy.exc.DatabaseError as db_err:
        # Detect overlapping booking error
        if "Overlapping booking detected" in str(db_err):
            logging.warning(f"User '{get_current_user()}' attempted an overlapping booking.")
            log_event(
                get_current_user(),
                "Failure",
                "Booking",
                f"User attempted an overlapping booking for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}'",
            )
            messagebox.showwarning(
                title="Booking Error",
                message=f"You already have a booking during this time. Please select a different time slot.",
            )
        else:
            logging.error(f"Database error while creating booking: {db_err}")
            log_event(
                get_current_user(),
                "Failure",
                "Booking",
                f"Database error while creating booking for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}'",
            )
            messagebox.showerror(
                title="Database Error", message="An unexpected database error occurred. Please try again later."
            )
        raise

    except ValueError as val_err:
        # Handle user-input errors
        logging.error(f"Error while creating booking: {val_err}")
        log_event(
            get_current_user(),
            "Failure",
            "Booking",
            f"Error while creating booking for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}': {val_err}",
        )
        messagebox.showerror(title="Input Error", message=f"Booking creation failed: {val_err}")
        raise

    except Exception as exc:
        # Handle unexpected errors
        logging.error(f"Unexpected error while creating booking: {exc}")
        log_event(
            get_current_user(),
            "Failure",
            "Booking",
            f"Unexpected error while creating booking for desk '{desk_code}' from '{start_time_dt}' to '{end_time_dt}': {exc}",
        )
        messagebox.showerror(title="Error", message="An unexpected error occurred. Please try again later.")
        raise


# Function to check if the user has an active or next pending reservation
def check_user_current_or_next_booking(session_factory: Callable[[], Session]) -> dict | None:
    """Check if the user has an active or pending booking.

    param: session_factory: A callable that returns a SQLAlchemy session
    """
    try:
        user = get_current_user()

        with managed_session(session_factory) as session:
            # Fetch "Active" and "Pending" statuses
            active_status = session.execute(select(Status).where(Status.status_name == "Active")).scalar_one_or_none()
            pending_status = session.execute(
                select(Status).where(Status.status_name == "Pending")
            ).scalar_one_or_none()
            if not active_status or not pending_status:
                raise ValueError("Required statuses ('Active' and 'Pending') not found in the database.")

            # Query for an active booking first
            active_booking = session.execute(
                select(Booking)
                .where(
                    Booking.user_name == user,
                    Booking.status_id == active_status.status_id,
                )
                .order_by(Booking.start_date)
            ).scalar_one_or_none()

            if active_booking:
                return {
                    "booking_id": active_booking.booking_id,
                    "desk_code": active_booking.desk_code,
                    "start_time": active_booking.start_date.strftime("%Y-%m-%d %H:%M"),
                    "end_time": active_booking.end_date.strftime("%Y-%m-%d %H:%M"),
                    "status": active_status.status_name,
                }

            # PROJECT REQUIREMENT: subquery
            # If no active booking, query the next pending booking
            next_pending_booking = (
                session.execute(
                    select(Booking)
                    .where(
                        Booking.user_name == user,
                        Booking.status_id  # == pending_status.status_id,
                        == (select(Status.status_id).where(Status.status_name == "Pending")).scalar_subquery(),
                        Booking.start_date > datetime.now(),
                    )
                    .order_by(Booking.start_date)
                )
                .scalars()
                .first()
            )

            if next_pending_booking:
                return {
                    "booking_id": next_pending_booking.booking_id,
                    "desk_code": next_pending_booking.desk_code,
                    "start_time": next_pending_booking.start_date.strftime("%Y-%m-%d %H:%M"),
                    "end_time": next_pending_booking.end_date.strftime("%Y-%m-%d %H:%M"),
                    "status": pending_status.status_name,
                }

            # If neither active nor pending bookings are found, return None
            return None
    except Exception as exc:
        logging.error(f"Error while fetching user booking: {exc}")
        log_event(get_current_user(), "Failure", "Booking", f"Error while fetching next user booking: {exc}")
        messagebox.showerror(
            title="Error",
            message="An unexpected error occurred while fetching your booking. Please try again later.",
        )
        return None


def check_in_booking(session_factory: Callable[[], Session], booking_id: int) -> bool:
    """Mark a booking as 'Active' by updating its status."""
    try:
        user = get_current_user()

        with managed_session(session_factory) as session:
            # Get the status for "Active"
            active_status = session.execute(select(Status).where(Status.status_name == "Active")).scalar_one_or_none()
            if not active_status:
                raise ValueError("Active status not found in the database.")

            # Ensure the booking matches the provided booking_id
            booking = session.execute(select(Booking).where(Booking.booking_id == booking_id)).scalar_one_or_none()
            if not booking:
                raise ValueError("No valid booking found for check-in.")

            # Update booking status to Active
            booking.status_id = active_status.status_id
            session.commit()

            # Log the successful check-in
            logging.info(f"User '{user}' successfully checked in for booking {booking_id}.")
            log_event(
                user,
                "Success",
                "Check-in",
                f"User successfully checked in for booking ID: {booking_id}",
            )
            return True
    except Exception as exc:
        logging.error(f"Error during check-in for booking ID {booking_id}: {exc}")
        log_event(
            get_current_user(),
            "Failure",
            "Check-in",
            f"Error during check-in for booking ID {booking_id}: {exc}",
        )
        return False


def cancel_booking(session_factory: Callable[[], Session], booking_id: int) -> bool:
    """Cancel a booking by updating its status to 'Canceled'."""
    try:
        with managed_session(session_factory) as session:
            canceled_status = session.execute(
                select(Status).where(Status.status_name == "Canceled")
            ).scalar_one_or_none()
            if not canceled_status:
                raise ValueError("Canceled status not found in the database.")

            # Fetch the booking
            booking = session.execute(select(Booking).where(Booking.booking_id == booking_id)).scalar_one_or_none()
            if not booking:
                raise ValueError("Booking not found to cancel.")

            # Update status
            booking.status_id = canceled_status.status_id
            session.commit()
            logging.info(f"Booking {booking_id} successfully canceled.")
            return True
    except Exception as exc:
        logging.error(f"Error during booking cancellation: {exc}")
        return False


# PROJECT REQUIREMENT: complex query
def get_most_reserved_desk(event: Event, session_factory: Callable[[], Session]):
    """
    Query the database to find the most reserved desk with additional location details.

    :param event: The event that triggered the function
    :param session_factory: A callable that returns a SQLAlchemy session
    :return: A dictionary containing desk details, location details, and reservation count
    """
    try:
        with managed_session(session_factory) as session:
            stmt = (
                select(
                    Desk.desk_code,
                    Desk.local_id.label("desk_code"),
                    Floor.floor_name,
                    Office.office_name,
                    func.count(Booking.booking_id).label("reservation_count"),
                )
                .join(Booking, Booking.desk_code == Desk.desk_code)
                .join(Floor, Desk.floor_id == Floor.floor_id)
                .join(Office, Desk.office_id == Office.office_id)
                .group_by(Desk.desk_id, Desk.local_id, Floor.floor_name, Office.office_name)
                .order_by(desc(func.count(Booking.booking_id)))
                .limit(1)
            )

        result = session.execute(stmt).first()

        if result:
            messagebox.showinfo(
                "Most Reserved Desk",
                "Most reserved desk details:\n"
                f"Desk code: '{result.desk_code}'\n"
                f"Floor name: '{result.floor_name}'\n"
                f"Office name: '{result.office_name}'\n"
                f"Reservation Count: {result.reservation_count}",
            )
        else:
            messagebox.showinfo("Most Reserved Desk", "No bookings found.")

    except Exception as e:
        return {"error": f"An error occurred: {e}"}


# PROJECT REQUIREMENT: query view
def get_most_frequent_booker(event: Event, session_factory: Callable[[], Session]):
    """
    Use SQLAlchemy's select to find the user with the most reservations.

    :param event: The event that triggered the function
    :param session_factory: A callable that returns a SQLAlchemy session
    :return: A dictionary containing user details and reservation count
    """
    try:
        with managed_session(session_factory) as session:
            with managed_session(session_factory) as session:
                stmt = select(MostFrequentUser).order_by(MostFrequentUser.reservation_count.desc()).limit(1)
                result = session.execute(stmt).scalars().first()

            if result:
                messagebox.showinfo(
                    "Most Frequent User",
                    "Most frequent user details:\n"
                    f"User name: '{result.user_name}'\n"
                    f"Reservation Count: {result.reservation_count}",
                )
            else:
                messagebox.showinfo("Most Frequent User", "No reservations found.")

    except Exception as e:
        return {"error": f"An error occurred: {e}"}
