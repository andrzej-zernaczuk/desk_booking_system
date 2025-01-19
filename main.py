import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from db.sql_db import initialize_app_db
from db.session_management import initialize_shared_session, close_shared_session, safe_session_factory
from backend_operations.user_login import login
from backend_operations.bookings_backend import create_booking, get_most_reserved_desk, get_most_frequent_booker
from gui_operations.bookings_gui import initialize_booking_info
from gui_operations.gui_utils import show_frame, center_window, on_login_success
from gui_operations.dropdowns_gui import (
    calculate_time_intervals,
    populate_office_dropdown,
    on_office_select,
    on_floor_select,
    reset_sector_selection,
    update_book_desk_button_text,
)


def start_tkinter_app():
    # Initialize shared session
    global shared_session
    shared_session = initialize_shared_session()
    if shared_session is None:
        logging.error("Failed to initialize shared session during app startup.")
        messagebox.showerror("Critical Error", "Application failed to initialize. Please restart.")
        return

    # main window
    root = tk.Tk()
    root.title("Desk Booking System by Andrzej Zernaczuk")
    root.resizable(False, True)  # Disable resizing in width
    root.minsize(width=1000, height=600)
    root.after(10, lambda: center_window(root))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    ################################################### LOGIN #################################################################################
    # First Screen: Login Screen
    login_frame = tk.Frame(root)
    login_frame.grid(row=0, column=0, sticky="nsew")
    login_frame.grid_rowconfigure(0, weight=1)
    login_frame.grid_rowconfigure(7, weight=1)
    login_frame.grid_columnconfigure(0, weight=1)
    login_frame.grid_columnconfigure(2, weight=1)

    instructions_label = tk.Label(login_frame, text="Please login:", font=("Arial", 24))
    instructions_label.grid(row=1, column=1, pady=(10, 20))

    # Email label and entry field
    email_label = tk.Label(login_frame, text="Email address:", font=("Arial", 16))
    email_label.grid(row=2, column=1, sticky="w", padx=10)
    email_entry = tk.Entry(login_frame, font=("Arial", 12), width=40)
    email_entry.grid(row=3, column=1, pady=5)

    # Password label and entry field
    password_label = tk.Label(login_frame, text="Password:", font=("Arial", 16))
    password_label.grid(row=4, column=1, sticky="w", padx=10)
    password_entry = tk.Entry(login_frame, font=("Arial", 12), width=40, show="*")  # `show="*"` masks the input
    password_entry.grid(row=5, column=1, pady=5)

    session_factory = safe_session_factory(shared_session)
    # Login button
    login_button = tk.Button(
        login_frame,
        text="Login",
        font=("Arial", 12),
        command=lambda: (
            login(
                email_entry.get(),
                password_entry.get(),
                lambda: on_login_success(
                    session_factory,
                    booking_details_label,
                    check_in_button,
                    cancel_button,
                    desk_selecton_frame,
                    bookings_frame,
                    booking_info_frame,
                    floor_image_frame,
                    all_frames,
                ),
            )
        ),
    )
    login_button.grid(row=6, column=1, pady=(20, 10))
    ################################################### DESK SELECTION ########################################################################
    # Second Screen: Desk Selection
    desk_selecton_frame = tk.Frame(root)
    desk_selecton_frame.grid_rowconfigure(0, weight=1)
    desk_selecton_frame.grid_columnconfigure(1, weight=0)
    desk_selecton_frame.grid_columnconfigure(1, weight=0)
    desk_selecton_frame.grid_columnconfigure(2, weight=1)

    # Left frame for dropdowns
    dropdowns_frame = tk.Frame(desk_selecton_frame, width=300)
    dropdowns_frame.grid(row=0, column=0, sticky="nsw")
    dropdowns_frame.grid_propagate(False)

    # Add a vertical separator
    separator_frame = tk.Frame(desk_selecton_frame, width=1, bg="lightgrey")
    separator_frame.grid(row=0, column=1, sticky="ns")

    # Right frame for the image and info
    bookings_frame = tk.Frame(desk_selecton_frame)
    bookings_frame.grid(row=0, column=2, sticky="nsew")
    bookings_frame.grid_rowconfigure(0, weight=1)
    bookings_frame.grid_rowconfigure(1, weight=5)
    bookings_frame.grid_columnconfigure(0, weight=1)

    # Date Selection
    date_label = tk.Label(dropdowns_frame, text="Select booking date:", font=("Arial", 12))
    date_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

    date_dropdown = ttk.Combobox(dropdowns_frame, state="readonly")
    date_dropdown.grid(row=1, column=0, padx=10, sticky="w")

    # Populate the date dropdown with available dates (today + 6 days)
    today = datetime.now()
    available_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    date_dropdown["values"] = available_dates
    date_dropdown.set(available_dates[0])  # Default to today's date

    # debug set today to yesterday 23:45
    if today.hour == 23 and today.minute >= 30:
        # Update the date dropdown to the next day
        next_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        date_dropdown.set(next_date)

    # Time selection
    suggested_start_time, suggested_end_time, possible_start_times, possible_end_times = calculate_time_intervals(
        date_dropdown.get()
    )
    # Start Time Dropdown
    start_time_label = tk.Label(dropdowns_frame, text="Start Time:", font=("Arial", 12))
    start_time_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

    start_time_dropdown = ttk.Combobox(dropdowns_frame, state="readonly")
    start_time_dropdown.grid(row=3, column=0, padx=10, sticky="w")
    start_time_dropdown["values"] = possible_start_times
    start_time_dropdown.set(suggested_start_time)

    # End Time Dropdown
    end_time_label = tk.Label(dropdowns_frame, text="End Time:", font=("Arial", 12))
    end_time_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

    end_time_dropdown = ttk.Combobox(dropdowns_frame, state="readonly")
    end_time_dropdown.grid(row=5, column=0, padx=10, sticky="w")
    end_time_dropdown["values"] = possible_end_times
    end_time_dropdown.set(suggested_end_time)

    # Dropdown for Office
    office_label = tk.Label(dropdowns_frame, text="Select office:", font=("Arial", 12))
    office_label.grid(row=6, column=0, padx=10, pady=(10, 5), sticky="w")

    office_dropdown = ttk.Combobox(dropdowns_frame, values=populate_office_dropdown(session_factory), state="readonly")
    office_dropdown.grid(row=7, column=0, padx=10, sticky="w")
    office_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda event: on_office_select(
            event, session_factory, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, book_desk_button
        ),
    )

    # Dropdown for Floor
    floor_label = tk.Label(dropdowns_frame, text="Select office floor:", font=("Arial", 12))
    floor_label.grid(row=8, column=0, padx=10, pady=(10, 5), sticky="w")

    floor_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    floor_dropdown.grid(row=9, column=0, padx=10, sticky="w")
    floor_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda event: on_floor_select(
            event,
            session_factory,
            office_dropdown,
            floor_dropdown,
            sector_dropdown,
            desk_dropdown,
            book_desk_button,
            image_label,
        ),
    )

    # Dropdown for Sector
    sector_label = tk.Label(dropdowns_frame, text="Select floor sector:", font=("Arial", 12))
    sector_label.grid(row=10, column=0, padx=10, pady=(10, 5), sticky="w")

    # Create a frame to hold the sector dropdown and reset button
    sector_frame = tk.Frame(dropdowns_frame)
    sector_frame.grid(row=11, column=0, padx=10, sticky="w")

    sector_dropdown = ttk.Combobox(sector_frame, state="disabled", width=20)
    sector_dropdown.grid(row=0, column=0, sticky="w")

    # Reset Button (X mark)
    reset_button = tk.Button(
        sector_frame,
        text="X",
        font=("Arial", 10),
        width=2,
        command=lambda: reset_sector_selection(
            session_factory, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, book_desk_button
        ),
    )
    reset_button.grid(row=0, column=1, padx=(10, 0), sticky="w")

    # Dropdown for desk
    desk_label = tk.Label(dropdowns_frame, text="Select desk:", font=("Arial", 12))
    desk_label.grid(row=12, column=0, padx=10, pady=(10, 5), sticky="w")

    desk_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    desk_dropdown.grid(row=13, column=0, padx=10, sticky="w")
    desk_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda event: update_book_desk_button_text(
            event, session_factory, sector_dropdown, desk_dropdown, book_desk_button
        ),
    )

    # Button for booking the desk
    book_desk_button = tk.Button(
        dropdowns_frame, text=f"Book desk {desk_dropdown.get()}", width=35, font=("Arial", 12), state="disabled"
    )
    book_desk_button.grid(row=14, column=0, padx=10, pady=(20, 5), sticky="we")
    book_desk_button.bind(
        "<Button-1>",
        lambda event: (
            create_booking(
                event,
                session_factory,
                desk_dropdown.get(),
                date_dropdown.get(),
                start_time_dropdown.get(),
                end_time_dropdown.get(),
            ),
            initialize_booking_info(
                session_factory,
                booking_details_label,
                check_in_button,
                cancel_button,
                bookings_frame,
                booking_info_frame,
                floor_image_frame,
            ),
        ),
    )
    book_desk_button.grid_remove()
    ################################################### Statistics ########################################################################
    statistics_tools_label = tk.Label(dropdowns_frame, text="Statistics", font=("Arial", 12))
    statistics_tools_label.grid(row=15, column=0, padx=10, pady=(10, 5), sticky="w")

    # Create a frame to hold the sector dropdown and reset button
    statistics_tools_frame = tk.Frame(dropdowns_frame)
    statistics_tools_frame.grid(row=16, column=0, padx=10, sticky="we")

    # Button for displaying most reserved desk
    most_reserved_desk_button = tk.Button(
        statistics_tools_frame, text="Most Reserved Desk", font=("Arial", 11), state="normal"
    )
    most_reserved_desk_button.grid(row=0, column=0, padx=(0, 8), sticky="w")
    most_reserved_desk_button.bind("<Button-1>", lambda event: get_most_reserved_desk(event, session_factory))

    most_frequent_user_button = tk.Button(
        statistics_tools_frame, text="Most Frequent User", font=("Arial", 11), state="normal"
    )
    most_frequent_user_button.grid(row=0, column=1, sticky="e")
    most_frequent_user_button.bind(
        "<Button-1>",
        lambda event: get_most_frequent_booker(event, session_factory),
    )
    ################################################### BOOKING INFO ########################################################################
    # Booking info Frame
    booking_info_frame = tk.Frame(bookings_frame, bg="#cccccc", height=120)
    booking_info_frame.grid(row=0, column=0, padx=20, pady=(0, 10), sticky="new")
    booking_info_frame.grid_columnconfigure(0, weight=1)
    booking_info_frame.grid_propagate(False)

    # First column: Booking Details Label
    booking_info_label = tk.Label(
        booking_info_frame, text="Your next booking details:", font=("Arial", 18, "bold"), bg="#cccccc"
    )
    booking_info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

    # Booking Details Label
    booking_details_label = tk.Label(
        booking_info_frame,
        text="Desk: N/A, Start: N/A, End: N/A",
        font=("Arial", 14),
        bg="#cccccc",
    )
    booking_details_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

    # Buttons
    button_style = {
        "font": ("Arial", 12),
        "bg": "#cccccc",
        "relief": "flat",
        "width": 12,
        "height": 2,
    }  # Bigger buttons

    check_in_button = tk.Button(booking_info_frame, text="Check In", state="disabled", **button_style)
    check_in_button.grid(row=0, column=1, padx=20, pady=(10, 5), sticky="e")

    cancel_button = tk.Button(booking_info_frame, text="Cancel", state="disabled", **button_style)
    cancel_button.grid(row=1, column=1, padx=20, pady=(10, 5), sticky="e")

    # Image display Frame
    floor_image_frame = tk.Frame(bookings_frame)
    floor_image_frame.grid(row=1, column=0, sticky="nsew")
    floor_image_frame.grid_rowconfigure(1, weight=5)
    floor_image_frame.grid_columnconfigure(0, weight=1)

    image_label = tk.Label(floor_image_frame, text="Select an office and floor to view the layout", font=("Arial", 16))
    image_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    # Initially, show the login frame
    all_frames = [login_frame, desk_selecton_frame]
    show_frame(login_frame, all_frames)

    def on_closing():
        # TODO: Update user status to offline
        close_shared_session(shared_session)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        initialize_app_db()
        logging.info("Application initialized successfully!")
    except Exception as error:
        logging.error(f"Application initialization failed: {error} \n :(((")
        exit(1)

    # Start the GUI application
    start_tkinter_app()
