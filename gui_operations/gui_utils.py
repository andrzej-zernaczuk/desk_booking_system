from tkinter import Tk, Frame, Label, Button
from typing import Callable
from sqlalchemy.orm import Session
from screeninfo import get_monitors

from gui_operations.bookings_gui import initialize_booking_info


def show_frame(frame: Frame, all_frames: list[Frame]):
    """Show a frame and hide all other frames.

    :param frame: The frame to show
    :param all_frames: A list of all frames
    """
    # Hide all frames
    for f in all_frames:
        f.grid_forget()

    # Show the selected frame
    frame.grid(row=0, column=0, sticky="nsew")

    # Force an update to ensure all widgets are properly displayed
    frame.update_idletasks()


def on_login_success(
    session_factory: Callable[[], Session],
    booking_details_label: Label,
    check_in_button: Button,
    cancel_button: Button,
    desk_selecton_frame: Frame,
    bookings_frame: Frame,
    booking_info_frame: Frame,
    floor_image_frame: Frame,
    all_frames: list[Frame],
):
    """Callback to transition to the success frame.

    :param desk_selecton_frame: The frame to be shown
    :param all_frames: A list of all frames
    """
    show_frame(desk_selecton_frame, all_frames)
    initialize_booking_info(
        session_factory,
        booking_details_label,
        check_in_button,
        cancel_button,
        bookings_frame,
        booking_info_frame,
        floor_image_frame,
    )


def center_window(window: Tk):
    """Center the window on the screen.

    :param window: The window to center
    """
    # Select primary monitor
    primary_monitor = get_monitors()[0]

    # Get screen width and height
    screen_width = primary_monitor.width
    screen_height = primary_monitor.height

    # Get the monitor's x and y position
    monitor_x = primary_monitor.x
    monitor_y = primary_monitor.y

    # Get the window's current width and height
    window.update_idletasks()  # Ensure all pending events have been processed
    window_width = window.winfo_width()
    window_height = window.winfo_height()

    # Calculate the position x and y to center the window
    x = monitor_x + (screen_width // 2) - (window_width // 2)
    y = monitor_y + (screen_height // 2) - (window_height // 2)

    # Set the geometry of the window (position only, no size)
    window.geometry(f"+{x}+{y}")
