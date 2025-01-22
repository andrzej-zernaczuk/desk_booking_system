import logging
from typing import Callable
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from tkinter import Button, Frame, Label, messagebox

from backend_operations.bookings_backend import check_user_current_or_next_booking, check_in_booking, cancel_booking
from backend_operations.user_login import get_current_user


def update_button_states(booking: dict, check_in_button: Button):
    """Update button states based on current time."""
    current_time = datetime.now()
    booking_start = datetime.strptime(booking["start_time"], "%Y-%m-%d %H:%M")

    # Enable 'Check In' button 15 minutes before start and up to 30 minutes after start
    if (
        booking_start - timedelta(minutes=15) <= current_time <= booking_start + timedelta(minutes=30)
        and not booking["status"] == "Active"
    ):
        check_in_button.config(state="normal")
    else:
        check_in_button.config(state="disabled")


def show_booking_info(
    booking: dict,
    booking_info_frame: Frame,
    booking_details_label: Label,
    check_in_button: Button,
):
    """Show booking info in the popup."""
    booking_details_label.config(
        text=f"Desk: {booking['desk_code']}, Start: {booking['start_time']}, End: {booking['end_time']}."
    )
    update_button_states(booking, check_in_button)
    booking_info_frame.grid()


def initialize_booking_info(
    session_factory: Callable[[], Session],
    booking_details_label: Label,
    check_in_button: Button,
    cancel_button: Button,
    bookings_frame: Frame,
    booking_info_frame: Frame,
    floor_image_frame: Frame,
):
    """Check for user's next booking and display it if exists."""
    try:
        # Fetch the user's next booking
        next_booking = check_user_current_or_next_booking(session_factory)

        logging.info(f"Current booking: {next_booking}")

        if next_booking:
            # Display the booking info
            show_booking_info(
                next_booking,
                booking_info_frame,
                booking_details_label,
                check_in_button,
            )

            # Enable cancel button
            cancel_button.config(
                state="normal",
                command=lambda: handle_cancel_booking(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )

            # Enable/Disable the check-in button based on the booking
            update_button_states(next_booking, check_in_button)
            check_in_button.config(
                command=lambda: handle_check_in(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )

            # Show the booking info frame
            toggle_booking_info_frame(True, bookings_frame, booking_info_frame, floor_image_frame)
        else:
            # No booking, hide the frame
            toggle_booking_info_frame(False, bookings_frame, booking_info_frame, floor_image_frame)
    except Exception as exc:
        logging.error(f"Error initializing booking info: {exc}")
        messagebox.showerror("Error", "Failed to fetch booking information.")


def toggle_booking_info_frame(show: bool, bookings_frame: Frame, booking_info_frame: Frame, floor_image_frame: Frame):
    """
    Toggles the visibility of the booking_info_frame and adjusts row weights.

    :param show: Boolean indicating whether to show or hide the booking_info_frame.
    :param booking_info_frame: The frame to show or hide.
    :param bookings_frame: The parent frame containing the booking_info_frame.
    """
    logging.info(f"Toggling booking_info_frame. Show: {show}")

    if show:
        booking_info_frame.grid()
        bookings_frame.grid_rowconfigure(0, weight=1)
        floor_image_frame.grid_rowconfigure(1, weight=5)
    else:
        booking_info_frame.grid_remove()
        bookings_frame.grid_rowconfigure(0, weight=0)
        floor_image_frame.grid_rowconfigure(0, weight=1)


def handle_cancel_booking(
    session_factory: Callable[[], Session],
    current_booking: dict,
    booking_info_frame: Frame,
    booking_details_label: Label,
    check_in_button: Button,
    cancel_button: Button,
    bookings_frame: Frame,
    floor_image_frame: Frame,
):
    """Handle the cancel booking action for the given booking."""
    try:
        user = get_current_user()

        # Cancel the current booking
        if not cancel_booking(session_factory, current_booking["booking_id"]):
            messagebox.showerror("Error", "Failed to cancel booking. Please try again.")
            return

        # Notify the user
        messagebox.showinfo(
            "Success",
            "Your booking has been successfully canceled! Details:\n"
            f"Desk code: '{current_booking['desk_code']}'\n"
            f"Start time: '{current_booking["start_time"]}'\n"
            f"End time: '{current_booking["end_time"]}'",
        )

        # Fetch the next booking from the backend
        next_booking = check_user_current_or_next_booking(session_factory)

        if next_booking:
            # Update booking info with the next booking
            booking_details_label.config(
                text=f"Desk: {next_booking['desk_code']}, Start: {next_booking['start_time']}, End: {next_booking['end_time']}."
            )
            # Update button states for the new booking
            update_button_states(next_booking, check_in_button)
            check_in_button.config(
                command=lambda: handle_check_in(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )
            cancel_button.config(
                state="normal",
                command=lambda: handle_cancel_booking(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )
            toggle_booking_info_frame(True, bookings_frame, booking_info_frame, floor_image_frame)
        else:
            # If no more bookings, hide the frame
            toggle_booking_info_frame(False, bookings_frame, booking_info_frame, floor_image_frame)

    except Exception as exc:
        logging.error(f"Error during booking cancellation for {user}: {exc}")
        messagebox.showerror("Error", "Failed to cancel booking. Please try again.")


def handle_check_in(
    session_factory: Callable[[], Session],
    current_booking: dict,
    booking_info_frame: Frame,
    booking_details_label: Label,
    check_in_button: Button,
    cancel_button: Button,
    bookings_frame: Frame,
    floor_image_frame: Frame,
):
    """Handle the check-in action for the given booking."""
    try:
        # Perform the check-in using the backend
        if not check_in_booking(session_factory, current_booking["booking_id"]):
            messagebox.showerror("Error", "Failed to check in. Please try again.")
            return

        # Notify the user of the successful check-in
        messagebox.showinfo("Success", "You have successfully checked in.")

        # Fetch the next booking (if any) and update the UI
        next_booking = check_user_current_or_next_booking(session_factory)

        if next_booking:
            # Update booking info with the next booking
            booking_details_label.config(
                text=f"Desk: {next_booking['desk_code']}, Start: {next_booking['start_time']}, End: {next_booking['end_time']}."
            )
            # Update button states for the new booking
            update_button_states(next_booking, check_in_button)
            check_in_button.config(
                command=lambda: handle_check_in(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )
            cancel_button.config(
                state="normal",
                command=lambda: handle_cancel_booking(
                    session_factory,
                    next_booking,
                    booking_info_frame,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    bookings_frame,
                    floor_image_frame,
                ),
            )
            toggle_booking_info_frame(True, bookings_frame, booking_info_frame, floor_image_frame)
        else:
            # If no more bookings, hide the frame
            toggle_booking_info_frame(False, bookings_frame, booking_info_frame, floor_image_frame)

    except Exception as exc:
        logging.error(f"Error during check-in handling: {exc}")
        messagebox.showerror("Error", "An unexpected error occurred during check-in. Please try again.")
