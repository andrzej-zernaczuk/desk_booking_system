import logging
from PIL import Image, ImageTk
from typing import Callable, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from tkinter import messagebox, Event, Button, Label
from tkinter.ttk import Combobox

from backend_operations.utils import resource_path
from backend_operations.log_utils import log_event
from backend_operations.user_login import get_current_user
from backend_operations.dropdowns_backend import (
    get_available_offices,
    get_floors_in_office,
    get_sectors_on_floor,
    get_desks_on_floor,
    get_desk_sector,
)


def calculate_time_intervals(selected_date_str: str) -> tuple:
    """Calculate available time intervals for start and end time.

    :param selected_date_str: The selected booking date as a string (YYYY-MM-DD).
    :return: A tuple containing suggested start time, suggested end time, all start times, and all end times.
    """
    # Current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.date()

    # Suggested start and end hours
    start_hour_sugg = datetime.combine(current_date, datetime.min.time()).replace(hour=8, minute=0, second=0)
    end_hour_sugg = datetime.combine(current_date, datetime.min.time()).replace(hour=16, minute=0, second=0)

    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    # Ensure the selected date is valid
    if selected_date < current_date:
        raise ValueError("Booking cannot be made for past dates.")

    suggested_start_time = None
    suggested_end_time = None
    all_start_times = []
    all_end_times = []

    # **Generate all valid start and end times for the entire day**
    # This now generates times for both current and future dates
    start_time_to_add = datetime.combine(selected_date, datetime.min.time()).replace(hour=0, minute=15)
    while start_time_to_add <= datetime.combine(selected_date, datetime.max.time()).replace(hour=23, minute=30):
        all_start_times.append(start_time_to_add.strftime("%H:%M"))
        start_time_to_add += timedelta(minutes=15)

    end_time_to_add = datetime.combine(selected_date, datetime.min.time()).replace(hour=0, minute=30)
    while end_time_to_add <= datetime.combine(selected_date, datetime.max.time()).replace(hour=23, minute=45):
        all_end_times.append(end_time_to_add.strftime("%H:%M"))
        end_time_to_add += timedelta(minutes=15)

    # **Logic for current date**
    if selected_date == current_date:
        current_minute = current_datetime.minute
        current_hour = current_datetime.hour

        # Round the current time to the next valid 15-minute interval
        rounded_minute = ((current_minute // 15) + 1) * 15
        if rounded_minute >= 60:
            current_hour += 1
            rounded_minute = 0

        earliest_start_time = current_datetime.replace(
            hour=current_hour, minute=rounded_minute, second=0, microsecond=0
        )

        # **Filter start times for the current date**
        # This ensures start times begin from the current time onwards
        all_start_times = [
            time_str
            for time_str in all_start_times
            if datetime.combine(selected_date, datetime.strptime(time_str, "%H:%M").time()) >= earliest_start_time
        ]

        # **Filter end times**
        # This ensures end times are only after the filtered start times
        all_end_times = [
            time_str
            for time_str in all_end_times
            if datetime.combine(selected_date, datetime.strptime(time_str, "%H:%M").time()) > earliest_start_time
        ]

        # Suggested start and end times for the current date
        if current_datetime < start_hour_sugg:
            suggested_start_time = start_hour_sugg.strftime("%H:%M")
            suggested_end_time = end_hour_sugg.strftime("%H:%M")
        elif end_hour_sugg - timedelta(minutes=15) > current_datetime >= start_hour_sugg:
            suggested_start_time = earliest_start_time.strftime("%H:%M")
            suggested_end_time = end_hour_sugg.strftime("%H:%M")
        else:
            suggested_start_time = earliest_start_time.strftime("%H:%M")
            suggested_end_time = (earliest_start_time + timedelta(minutes=15)).strftime("%H:%M")

    # **Logic for future dates**
    else:
        suggested_start_time = start_hour_sugg.strftime("%H:%M")
        suggested_end_time = end_hour_sugg.strftime("%H:%M")

    return suggested_start_time, suggested_end_time, all_start_times, all_end_times


def populate_office_dropdown(session_factory: Callable[[], Session]) -> list[str]:
    """Populate the office dropdown with available offices.

    :param session_factory: A callable that returns a SQLAlchemy session.
    """
    try:
        return get_available_offices(session_factory)
    except Exception as exc:
        logging.error(f"Error populating office dropdown: {exc}")
        return []


# runs after selection of office
def on_office_select(
    event: Event,
    shared_session: Callable[[], Session],
    office_dropdown: Combobox,
    floor_dropdown: Combobox,
    sector_dropdown: Combobox,
    desk_dropdown: Combobox,
    book_desk_button: Button,
) -> None:
    """Populate the floor dropdown based on the selected office.

    :param shared_session: The database session for querying.
    :param office_dropdown: The dropdown widget for offices.
    :param floor_dropdown: The dropdown widget for floors.
    :param sector_dropdown: The dropdown widget for sectors.
    :param desk_dropdown: The dropdown widget for desks.
    :param book_desk_button: The button for booking desks.
    """
    if shared_session is None:
        logging.error("Attempted to use shared_session before initialization.")
        messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
        return
    try:
        selected_office = office_dropdown.get()
        available_floors = get_floors_in_office(shared_session, selected_office)
        if not available_floors:
            messagebox.showerror("Error", "Unable to load floors. Please try again later.")
            return

        # Populate the floor dropdown
        floor_dropdown.set("")
        floor_dropdown["values"] = available_floors
        floor_dropdown.config(state="readonly")

        # Clear and disable the sector dropdown
        sector_dropdown.set("")
        sector_dropdown["values"] = []
        sector_dropdown.config(state="disabled")

        # Reset the desk dropdown
        desk_dropdown.set("")
        desk_dropdown["values"] = []
        desk_dropdown.config(state="disabled")

        # Hide the book desk button
        book_desk_button.grid_remove()
    except Exception as exc:
        logging.error(f"Error while populating floors for office: {exc}")
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


# runs after selection of sector
def on_floor_select(
    event: Any,
    shared_session: Callable[[], Session],
    office_dropdown: Combobox,
    floor_dropdown: Combobox,
    sector_dropdown: Combobox,
    desk_dropdown: Combobox,
    book_desk_button: Button,
    image_label: Label,
) -> None:
    """Populate the sector dropdown based on the selected floor.

    :param shared_session: The database session for querying.
    :param office_dropdown: The dropdown widget for offices.
    :param floor_dropdown: The dropdown widget for floors.
    :param sector_dropdown: The dropdown widget for sectors.
    :param desk_dropdown: The dropdown widget for desks.
    :param book_desk_button: The button for booking desks.
    :param image_label: The label for displaying the office layout image.
    """
    if shared_session is None:
        logging.error("Attempted to use shared_session before initialization.")
        messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
        return
    try:
        selected_office = office_dropdown.get()
        selected_floor = floor_dropdown.get()

        # Update the office layout image
        floor_template_path = resource_path(f"office_layouts/{selected_office}_{selected_floor}.png")
        try:
            floor_template = Image.open(floor_template_path)
            floor_template = floor_template.resize((600, 400), Image.Resampling.LANCZOS)
            floor_template_tk = ImageTk.PhotoImage(floor_template)
            image_label.config(image=floor_template_tk)  # type: ignore
            image_label.image = floor_template_tk  # type: ignore
        except FileNotFoundError:
            logging.error(f"Image for office: '{selected_office}', floor: '{selected_floor}' not found.")
            log_event(
                get_current_user(),
                "FAILURE",
                "Desk selection",
                f"No office layout found for office: '{selected_office}' and floor: '{selected_floor}'",
            )
            messagebox.showerror(
                "Error", f"No office layout found for office: '{selected_office}' and floor: '{selected_floor}'."
            )

        # Populate the sector dropdown
        available_sectors = get_sectors_on_floor(shared_session, selected_floor)
        if not available_sectors:
            logging.error(f"No sectors found for floor '{selected_floor}'.")
            log_event(
                get_current_user(),
                "FAILURE",
                "Desk selection",
                f"No sectors found for office: '{selected_office}' and floor: '{selected_floor}'",
            )
            messagebox.showerror(
                "Error", f"No sectors found for office: '{selected_office}' and floor: '{selected_floor}'."
            )

        else:
            sector_dropdown.set("")
            sector_dropdown["values"] = available_sectors
            sector_dropdown.config(state="readonly")

        # Populate the desks dropdown (without a sector initially)
        available_desks = get_desks_on_floor(shared_session, selected_floor, None)
        if not available_desks:
            logging.error(f"No desks found for floor '{selected_floor}'.")
            log_event(
                get_current_user(),
                "FAILURE",
                "Desk selection",
                f"No desks found for office: '{selected_office}' and floor: '{selected_floor}'",
            )
            messagebox.showerror(
                "Error", f"No desks found for office: '{selected_office}' and floor: '{selected_floor}'."
            )
            desk_dropdown.set("")
            desk_dropdown["values"] = []
            desk_dropdown.config(state="disabled")
        else:
            desk_dropdown.set("")
            desk_dropdown["values"] = available_desks
            desk_dropdown.config(state="readonly")

        # Hide the book desk button
        book_desk_button.grid_remove()

        # Bind sector selection to update the desks dropdown
        def on_sector_select(event):
            selected_sector = sector_dropdown.get()
            updated_desks = get_desks_on_floor(shared_session, selected_floor, selected_sector)
            desk_dropdown.set("")
            desk_dropdown["values"] = updated_desks
            desk_dropdown.config(state="readonly")

        sector_dropdown.bind("<<ComboboxSelected>>", on_sector_select)
    except Exception as exc:
        logging.error(
            f"Error while populating sectors and desks for office: '{selected_office}' and floor: '{selected_floor}': {exc}"
        )
        log_event(
            get_current_user(),
            "FAILURE",
            "Desk selection",
            f"Error while populating sectors and desks for office: '{selected_office}' and floor: '{selected_floor}': {exc}",
        )
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


def reset_sector_selection(
    shared_session: Callable[[], Session],
    office_dropdown: Combobox,
    floor_dropdown: Combobox,
    sector_dropdown: Combobox,
    desk_dropdown: Combobox,
    book_desk_button: Button,
) -> None:
    """Resets the sector selection, displaying all desks on the selected floor.

    :param shared_session: The database session for querying.
    :param office_dropdown: The dropdown widget for offices.
    :param floor_dropdown: The dropdown widget for floors.
    :param sector_dropdown: The dropdown widget for sectors.
    :param desk_dropdown: The dropdown widget for desks.
    :param book_desk_button: The button for booking desks.
    """
    if shared_session is None:
        logging.error("Attempted to use shared_session before initialization.")
        messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
        return

    selected_floor = floor_dropdown.get()
    if not selected_floor:
        logging.warning("No floor selected to reset sector.")
        messagebox.showwarning("Warning", "Please select a floor first.")
        return
    try:
        # Reset sector dropdown
        sector_dropdown.set("")
        sector_dropdown.config(state="disabled")

        # Fetch and populate all desks for the selected floor
        available_desks = get_desks_on_floor(shared_session, selected_floor, None)
        if not available_desks:
            desk_dropdown.set("")
            desk_dropdown["values"] = []
            logging.error(f"No desks found for office: '{office_dropdown.get()}' and floor: '{selected_floor}'.")
            log_event(
                get_current_user(),
                "FAILURE",
                "Desk selection",
                f"No desks found for office: '{office_dropdown.get()}' and floor: '{selected_floor}'",
            )
            messagebox.showerror("Error", "No desks available for the selected floor.")
        else:
            desk_dropdown.set("")
            desk_dropdown["values"] = available_desks
            desk_dropdown.config(state="readonly")

        # Hide the book desk button
        book_desk_button.grid_remove()
    except Exception as exc:
        logging.error(
            f"Error resetting sector selection for office: '{office_dropdown.get()}' and floor: '{selected_floor}'': {exc}"
        )
        log_event(
            get_current_user(),
            "FAILURE",
            "Desk selection",
            f"Error resetting sector selection for office: '{office_dropdown.get()}' and floor: '{selected_floor}'",
        )
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


def update_book_desk_button_text(
    event: Event,
    shared_session: Callable[[], Session],
    sector_dropdown: Combobox,
    desk_dropdown: Combobox,
    book_desk_button: Button,
) -> None:
    """
    Update the book desk button text based on the selected desk and populate the sector dropdown.

    :param event: The event triggered by desk selection.
    :param shared_session: The database session for querying.
    :param sector_dropdown: The dropdown widget for sectors.
    :param desk_dropdown: The dropdown widget for desks.
    :param book_desk_button: The button for booking desks.
    """
    selected_desk = desk_dropdown.get()  # Get the currently selected desk
    if selected_desk:
        book_desk_button.config(text=f"Book desk {selected_desk}", state="normal")
        book_desk_button.grid()
        try:
            populate_sector_dropdown_with_desk_sector(shared_session, sector_dropdown, selected_desk)
        except Exception as exc:
            logging.error(f"Error while fetching sector for desk '{selected_desk}': {exc}")
            sector_dropdown.set("")
            sector_dropdown.config(state="disabled")
    else:
        book_desk_button.config(text="Select a desk to book", state="disabled")
        book_desk_button.grid_remove()
        sector_dropdown.set("")
        sector_dropdown.config(state="disabled")


def populate_sector_dropdown_with_desk_sector(
    shared_session: Callable[[], Session], sector_dropdown: Combobox, selected_desk: str
) -> None:
    """Populate the sector dropdown based on the selected desk.

    :param shared_session: The database session for querying.
    :param sector_dropdown: The dropdown widget for sectors.
    :param selected_desk: The selected desk code.
    """
    sector_name = get_desk_sector(shared_session, selected_desk)
    if not sector_name:
        logging.error(f"No sector found for desk '{selected_desk}'.")
        log_event(get_current_user(), "FAILURE", "Desk selection", f"No sector found for desk: '{selected_desk}'")
        messagebox.showerror("Error", f"No sector found for desk: '{selected_desk}'.")
        sector_dropdown.set("")
        sector_dropdown.config(state="disabled")
    else:
        sector_dropdown.set(sector_name)
        sector_dropdown.config(state="readonly")
