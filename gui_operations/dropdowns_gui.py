import logging
from PIL import Image, ImageTk
from typing import Callable, Any
from sqlalchemy.orm import Session
from tkinter import messagebox
from tkinter.ttk import Combobox, Button, Label

from backend_operations.log_utils import log_event
from backend_operations.user_login import get_current_user
from backend_operations.dropdowns_backend import (
    get_available_offices,
    get_floors_in_office,
    get_sectors_on_floor,
    get_desks_on_floor,
    get_desk_sector
)


def populate_office_dropdown(shared_session: Callable) -> list[str]:
    if shared_session is None:
        logging.error("Attempted to use shared_session before initialization.")
        messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
        return
    try:
        return get_available_offices(shared_session)
    except Exception as exc:
        logging.error(f"Error while populating offices: {exc}")
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


# runs after selection of office
def on_office_select(
        event: Any,
        shared_session: Session,
        office_dropdown: Combobox,
        floor_dropdown: Combobox,
        sector_dropdown: Combobox,
        desk_dropdown: Combobox,
        book_desk_button: Button
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
        available_floors = get_floors_in_office(lambda: shared_session, selected_office)
        if not available_floors:
            messagebox.showerror("Error", "Unable to load floors. Please try again later.")
            return

        # Populate the floor dropdown
        floor_dropdown.set("")
        floor_dropdown['values'] = available_floors
        floor_dropdown.config(state="readonly")

        # Clear and disable the sector dropdown
        sector_dropdown.set("")
        sector_dropdown['values'] = []
        sector_dropdown.config(state="disabled")

        # Reset the desk dropdown
        desk_dropdown.set("")
        desk_dropdown['values'] = []
        desk_dropdown.config(state="disabled")

        # Hide the book desk button
        book_desk_button.grid_remove()
    except Exception as exc:
        logging.error(f"Error while populating floors for office: {exc}")
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


# runs after selection of sector
def on_floor_select(
        event: Any,
        shared_session: Session,
        office_dropdown: Combobox,
        floor_dropdown: Combobox,
        sector_dropdown: Combobox,
        desk_dropdown: Combobox,
        book_desk_button: Button,
        image_label: Label
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
        print(sector_dropdown)
        print(desk_dropdown)
        print(floor_dropdown)
        selected_office = office_dropdown.get()
        selected_floor = floor_dropdown.get()

        # Update the office layout image
        floor_template_path = f"office_layouts/{selected_office}_{selected_floor}.png"
        try:
            floor_template = Image.open(floor_template_path)
            floor_template = floor_template.resize((600, 400), Image.Resampling.LANCZOS)
            floor_template_tk = ImageTk.PhotoImage(floor_template)
            image_label.config(image=floor_template_tk)
            image_label.image = floor_template_tk
        except FileNotFoundError:
            logging.error(f"Image for office: '{selected_office}', floor: '{selected_floor}' not found.")
            log_event(get_current_user(), "FAILURE", "Desk selection", f"No office layout found for office: '{selected_office}' and floor: '{selected_floor}'")
            messagebox.showerror("Error", f"No office layout found for office: '{selected_office}' and floor: '{selected_floor}'.")

        # Populate the sector dropdown
        available_sectors = get_sectors_on_floor(lambda: shared_session, selected_floor)
        if not available_sectors:
            logging.error(f"No sectors found for floor '{selected_floor}'.")
            log_event(get_current_user(), "FAILURE", "Desk selection", f"No sectors found for office: '{selected_office}' and floor: '{selected_floor}'")
            messagebox.showerror("Error", f"No sectors found for office: '{selected_office}' and floor: '{selected_floor}'.")

        else:
            sector_dropdown.set("")
            sector_dropdown['values'] = available_sectors
            sector_dropdown.config(state="readonly")

        # Populate the desks dropdown (without a sector initially)
        available_desks = get_desks_on_floor(lambda: shared_session, selected_floor, None)
        if not available_desks:
            logging.error(f"No desks found for floor '{selected_floor}'.")
            log_event(get_current_user(), "FAILURE", "Desk selection", f"No desks found for office: '{selected_office}' and floor: '{selected_floor}'")
            messagebox.showerror("Error", f"No desks found for office: '{selected_office}' and floor: '{selected_floor}'.")
            desk_dropdown.set("")
            desk_dropdown['values'] = []
            desk_dropdown.config(state="disabled")
        else:
            desk_dropdown.set("")
            desk_dropdown['values'] = available_desks
            desk_dropdown.config(state="readonly")

        # Hide the book desk button
        book_desk_button.grid_remove()

        # Bind sector selection to update the desks dropdown
        def on_sector_select(event):
            selected_sector = sector_dropdown.get()
            updated_desks = get_desks_on_floor(lambda: shared_session, selected_floor, selected_sector)
            desk_dropdown.set("")
            desk_dropdown['values'] = updated_desks
            desk_dropdown.config(state="readonly")

        sector_dropdown.bind("<<ComboboxSelected>>", on_sector_select)
    except Exception as exc:
        logging.error(f"Error while populating sectors and desks for office: '{selected_office}' and floor: '{selected_floor}': {exc}")
        log_event(get_current_user(), "FAILURE", "Desk selection", f"Error while populating sectors and desks for office: '{selected_office}' and floor: '{selected_floor}': {exc}")
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")


def reset_sector_selection(
        shared_session: Session,
        office_dropdown: Combobox,
        floor_dropdown: Combobox,
        sector_dropdown: Combobox,
        desk_dropdown: Combobox,
        book_desk_button: Button
    ) -> None:
    """Resets the sector selection, displaying all desks on the selected floor.

    :param shared_session: The database session for querying.
    :param office_dropdown: The dropdown widget for offices.
    :param floor_dropdown: The dropdown widget for floors.
    :param sector_dropdown: The dropdown widget for sectors.
    :param desk_dropdown: The dropdown widget for desks.
    :param book_desk_button: The button for booking desks.
    """
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
        available_desks = get_desks_on_floor(lambda: shared_session, selected_floor, None)
        if not available_desks:
            desk_dropdown.set("")
            desk_dropdown['values'] = []
            logging.error(f"No desks found for office: '{office_dropdown.get()}' and floor: '{selected_floor}'.")
            log_event(get_current_user(), "FAILURE", "Desk selection", f"No desks found for office: '{office_dropdown.get()}' and floor: '{selected_floor}'")
            messagebox.showerror("Error", "No desks available for the selected floor.")
        else:
            desk_dropdown.set("")
            desk_dropdown['values'] = available_desks
            desk_dropdown.config(state="readonly")

        # Hide the book desk button
        book_desk_button.grid_remove()
    except Exception as exc:
        logging.error(f"Error resetting sector selection for office: '{office_dropdown.get()}' and floor: '{selected_floor}'': {exc}")
        log_event(get_current_user(), "FAILURE", "Desk selection", f"Error resetting sector selection for office: '{office_dropdown.get()}' and floor: '{selected_floor}'")
        messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")



def update_book_desk_button_text(
        shared_session: Session,
        sector_dropdown: Combobox,
        desk_dropdown: Combobox,
        book_desk_button: Button
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
        shared_session: Session,
        sector_dropdown: Combobox,
        selected_desk: str
    ) -> None:
    """Populate the sector dropdown based on the selected desk.

    :param shared_session: The database session for querying.
    :param sector_dropdown: The dropdown widget for sectors.
    :param selected_desk: The selected desk code.
    """
    sector_name = get_desk_sector(lambda: shared_session, selected_desk)
    if not sector_name:
        logging.error(f"No sector found for desk '{selected_desk}'.")
        log_event(get_current_user(), "FAILURE", "Desk selection", f"No sector found for desk: '{selected_desk}'")
        messagebox.showerror("Error", f"No sector found for desk: '{selected_desk}'.")
        sector_dropdown.set("")
        sector_dropdown.config(state="disabled")
    else:
        sector_dropdown.set(sector_name)
        sector_dropdown.config(state="readonly")