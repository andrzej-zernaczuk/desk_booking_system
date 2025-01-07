import os
import logging
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv

from utils import show_frame, center_window, on_success
from db.sql_db import create_tables, preload_data, Session
from users_operations.user_login import login
from dropdown_operations import get_available_offices, get_floors_in_office, get_sectors_on_floor


def initialize_app_db():
    """Initialize the application by setting up the database."""
    try:
        create_tables()  # Create tables
        preload_data()   # Preload data
    except (Exception, ValueError) as error:
        logging.error(f"Error during database initialization: {error}")
        raise


def start_tkinter_app():
    load_dotenv(".env")
    debug_mode=os.getenv("debug_mode")
    if debug_mode:
        logging.info("Debug mode is ON: Skipping login.")
    else:
        logging.info("Debug mode is OFF: Login required.")


    def on_office_select(event):
        """Populate the floor dropdown based on the selected office."""
        selected_office = office_dropdown.get()
        available_floors = get_floors_in_office(selected_office, Session)

        # Populate the floor dropdown
        floor_dropdown.set("")
        floor_dropdown['values'] = available_floors
        floor_dropdown.config(state="readonly")

        # Clear and disable the sector dropdown
        sector_dropdown.set("")
        sector_dropdown['values'] = []
        sector_dropdown.config(state="disabled")

    def on_floor_select(event):
        """Populate the sector dropdown based on the selected floor."""
        selected_floor = floor_dropdown.get()
        available_sectors = get_sectors_on_floor(selected_floor, Session)

        # Populate the sector dropdown
        sector_dropdown.set("")
        sector_dropdown['values'] = available_sectors
        sector_dropdown.config(state="readonly")

    # main window
    root = tk.Tk()
    root.title("Desk Booking Systen by Andrzej Zernaczuk")
    root.resizable(False, True)  # Disable resizing in width
    root.minsize(width=1000, height=400)
    root.after(10, lambda: center_window(root))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

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

    # Second Screen: Success Screen
    success_frame = tk.Frame(root)

    # Dropdown for Office
    office_label = tk.Label(success_frame, text="Select office:", font=("Arial", 12))
    office_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

    available_offices = get_available_offices(Session)
    office_dropdown = ttk.Combobox(success_frame, values=available_offices, state="readonly")
    office_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    office_dropdown.bind("<<ComboboxSelected>>", on_office_select)

    # Dropdown for Floor
    floor_label = tk.Label(success_frame, text="Select office floor:", font=("Arial", 12))
    floor_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

    floor_dropdown = ttk.Combobox(success_frame, state="disabled")
    floor_dropdown.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    floor_dropdown.bind("<<ComboboxSelected>>", on_floor_select)

    # Dropdown for Sector
    sector_label = tk.Label(success_frame, text="Select floor sector:", font=("Arial", 12))
    sector_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

    sector_dropdown = ttk.Combobox(success_frame, state="disabled")
    sector_dropdown.grid(row=5, column=0, padx=10, pady=5, sticky="w")

    # Image display on the right
    image_label = tk.Label(success_frame)
    image_label.grid(row=0, column=1, rowspan=6, padx=20, pady=20)

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

    root.mainloop()

if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        initialize_app_db()
        logging.info("Application initialized successfully")
    except Exception as error:
        logging.error(f"Application initialization failed: {error}")
        exit(1)  # Exit the application with a non-zero exit code for error

    # Start the GUI application
    start_tkinter_app()