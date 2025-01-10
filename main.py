import os
import logging
import tkinter as tk
from PIL import Image, ImageTk
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from tkinter import ttk, messagebox

from users_operations.user_login import login
from utils import show_frame, center_window, on_success
from db.sql_db import initialize_app_db
from db.session_management import initialize_shared_session, close_shared_session
from dropdown_operations import get_available_offices, get_floors_in_office, get_sectors_on_floor, get_desks_on_floor


def start_tkinter_app():
    load_dotenv(".env")
    debug_mode=os.getenv("debug_mode")
    if debug_mode:
        logging.info("Debug mode is ON: Skipping login.")
    else:
        logging.info("Debug mode is OFF: Login required.")

    # Initialize shared session
    global shared_session
    shared_session = initialize_shared_session()
    if shared_session is None:
        logging.error("Failed to initialize shared session during app startup.")
        messagebox.showerror("Critical Error", "Application failed to initialize. Please restart.")
        return

    # runs after selection of office
    def on_office_select(event, office_dropdown, floor_dropdown, sector_dropdown):
        """Populate the floor dropdown based on the selected office."""
        if shared_session is None:
            logging.error("Attempted to use shared_session before initialization.")
            messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
            return

        try:
            selected_office = office_dropdown.get()
            available_floors = get_floors_in_office(selected_office, lambda: shared_session)

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
        except Exception as exc:
            logging.error(f"Error while populating floors for office: {exc}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")

    # runs after selection of sector
    def on_floor_select(event, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, image_label):
        """Populate the sector dropdown based on the selected floor."""
        if shared_session is None:
            logging.error("Attempted to use shared_session before initialization.")
            messagebox.showerror("Error", "Application is not properly initialized. Please restart.")
            return

        try:
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
                messagebox.showerror("Error", f"No office layout found for office: '{selected_office}', floor: '{selected_floor}'.")

            # Populate the sector dropdown
            available_sectors = get_sectors_on_floor(selected_floor, lambda: shared_session)
            if not available_sectors:
                messagebox.showwarning("Warning", f"No sectors found for floor '{selected_floor}'.")
            else:
                sector_dropdown.set("")
                sector_dropdown['values'] = available_sectors
                sector_dropdown.config(state="readonly")

            # Populate the desks dropdown (without a sector initially)
            available_desks = get_desks_on_floor(selected_floor, None, lambda: shared_session)
            if not available_desks:
                messagebox.showwarning("Warning", f"No desks found for floor '{selected_floor}'.")
                desk_dropdown.set("")
                desk_dropdown['values'] = []
                desk_dropdown.config(state="disabled")
            else:
                desk_dropdown.set("")
                desk_dropdown['values'] = available_desks
                desk_dropdown.config(state="readonly")

            # Bind sector selection to update the desks dropdown
            def on_sector_select(event):
                selected_sector = sector_dropdown.get()
                updated_desks = get_desks_on_floor(selected_floor, selected_sector, lambda: shared_session)
                desk_dropdown.set("")
                desk_dropdown['values'] = updated_desks
                desk_dropdown.config(state="readonly")

            sector_dropdown.bind("<<ComboboxSelected>>", on_sector_select)

        except Exception as exc:
            logging.error(f"Error while populating sectors for floor: {exc}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")

    def reset_sector_selection(floor_dropdown, desk_dropdown, sector_dropdown, image_label):
        """Resets the sector selection, displaying all desks on the selected floor. """
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
            available_desks = get_desks_on_floor(selected_floor, None, lambda: shared_session)
            if available_desks:
                desk_dropdown.set("")
                desk_dropdown['values'] = available_desks
                desk_dropdown.config(state="readonly")
            else:
                desk_dropdown.set("")
                desk_dropdown['values'] = []
                messagebox.showinfo("No Desks", "No desks available for the selected floor.")
        except Exception as exc:
            logging.error(f"Error resetting sector selection for floor '{selected_floor}': {exc}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again later.")

    # main window
    root = tk.Tk()
    root.title("Desk Booking System by Andrzej Zernaczuk")
    root.resizable(False, True)  # Disable resizing in width
    root.minsize(width=1000, height=400)
    root.after(10, lambda: center_window(root))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    ################################################### LOGIN #################################################################################

    # Create a frame for the login screen
    login_frame = tk.Frame(root)
    instructions_label = tk.Label(login_frame, text="Please login:", font=("Arial", 24))
    instructions_label.pack(pady=(50, 25))

    # Email label and entry field
    email_label = tk.Label(login_frame, text="Email address:", font=("Arial", 16))
    email_label.pack(pady=(10, 5))
    email_entry = tk.Entry(login_frame, font=("Arial", 12), width=40)
    email_entry.pack()

    # Password label and entry field
    password_label = tk.Label(login_frame, text="Password:", font=("Arial", 16))
    password_label.pack(pady=(10, 5))
    password_entry = tk.Entry(login_frame, font=("Arial", 12), width=40, show="*")  # `show="*"` masks the input
    password_entry.pack()
    ################################################### DESK SELECTION ########################################################################

    # Second Screen: Success Screen
    success_frame = tk.Frame(root)
    success_frame.grid_rowconfigure(0, weight=1)
    success_frame.grid_columnconfigure(1, weight=1)


    # Left frame for dropdowns
    dropdowns_frame = tk.Frame(success_frame, width=300)
    dropdowns_frame.grid(row=0, column=0, sticky="ns")
    dropdowns_frame.grid_propagate(False)

    # Right frame for the image
    floor_image_frame = tk.Frame(success_frame)
    floor_image_frame.grid(row=0, column=1, sticky="nsew")
    floor_image_frame.grid_rowconfigure(0, weight=1)
    floor_image_frame.grid_columnconfigure(0, weight=1)

    # Image display on the right
    image_label = tk.Label(floor_image_frame, text="Select an office and floor to view the layout", font=("Arial", 16))
    image_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    # Dropdown for Office
    office_label = tk.Label(dropdowns_frame, text="Select office:", font=("Arial", 12))
    office_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

    available_offices = get_available_offices(lambda: shared_session)

    office_dropdown = ttk.Combobox(dropdowns_frame, values=available_offices, state="readonly")
    office_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    office_dropdown.bind("<<ComboboxSelected>>", lambda event: on_office_select(event, office_dropdown, floor_dropdown, sector_dropdown))


    # Dropdown for Floor
    floor_label = tk.Label(dropdowns_frame, text="Select office floor:", font=("Arial", 12))
    floor_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

    floor_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    floor_dropdown.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    floor_dropdown.bind("<<ComboboxSelected>>", lambda event: on_floor_select(event, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, image_label))


    # Dropdown for Sector
    sector_label = tk.Label(dropdowns_frame, text="Select floor sector:", font=("Arial", 12))
    sector_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

    # Create a frame to hold the sector dropdown and reset button
    sector_frame = tk.Frame(dropdowns_frame)
    sector_frame.grid(row=5, column=0, padx=10, pady=5, sticky="w")

    sector_dropdown = ttk.Combobox(sector_frame, state="disabled", width=20)
    sector_dropdown.grid(row=0, column=0, sticky="w")

    # Reset Button (X mark)
    reset_button = tk.Button(sector_frame, text="X", font=("Arial", 10), width=2, command=lambda: reset_sector_selection(floor_dropdown, desk_dropdown, sector_dropdown, image_label))
    reset_button.grid(row=0, column=1, padx=(10, 0), sticky="w")


    # Dropdown for desk
    desk_label = tk.Label(dropdowns_frame, text="Select desk:", font=("Arial", 12))
    desk_label.grid(row=6, column=0, padx=10, pady=(10, 5), sticky="w")

    desk_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    desk_dropdown.grid(row=7, column=0, padx=10, pady=5, sticky="w")

    all_frames = [login_frame, success_frame]

    # Login button
    login_button = tk.Button(
    login_frame,
    text="Login",
    font=("Arial", 12),
    command=lambda: (
        on_success(success_frame, all_frames)  # Skip login in debug mode
        if debug_mode
        else login(
            email_entry.get(),
            password_entry.get(),
            Session,
            lambda: on_success(success_frame, all_frames)
        )
    )
)

    login_button.pack(pady=(20, 0))

    # Initially, show the welcome frame
    show_frame(login_frame, all_frames)

    def on_closing():
        close_shared_session(shared_session)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        initialize_app_db()
        logging.info("Application initialized successfully")
    except Exception as error:
        logging.error(f"Application initialization failed: {error}")
        exit(1)

    # Start the GUI application
    start_tkinter_app()