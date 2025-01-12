import logging
import tkinter as tk
from tkinter import ttk, messagebox

from users_operations.user_login import login
from gui_utils import show_frame, center_window, on_success
from db.sql_db import initialize_app_db
from db.session_management import initialize_shared_session, close_shared_session
from dropdowns_gui import populate_office_dropdown, on_office_select, on_floor_select, reset_sector_selection, update_book_desk_button_text


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

    # Login button
    login_button = tk.Button(
        login_frame,
        text="Login",
        font=("Arial", 12),
        command=lambda: (
            login(
                email_entry.get(),
                password_entry.get(),
                lambda: on_success(success_frame, all_frames)
            )
        )
    )
    login_button.pack(pady=(20, 0))
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

    office_dropdown = ttk.Combobox(dropdowns_frame, values=populate_office_dropdown(lambda: shared_session), state="readonly")
    office_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    office_dropdown.bind("<<ComboboxSelected>>", lambda event: on_office_select(event, shared_session, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, book_desk_button))


    # Dropdown for Floor
    floor_label = tk.Label(dropdowns_frame, text="Select office floor:", font=("Arial", 12))
    floor_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

    floor_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    floor_dropdown.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    floor_dropdown.bind("<<ComboboxSelected>>", lambda event: on_floor_select(event, shared_session, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, book_desk_button, image_label))


    # Dropdown for Sector
    sector_label = tk.Label(dropdowns_frame, text="Select floor sector:", font=("Arial", 12))
    sector_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")

    # Create a frame to hold the sector dropdown and reset button
    sector_frame = tk.Frame(dropdowns_frame)
    sector_frame.grid(row=5, column=0, padx=10, pady=5, sticky="w")

    sector_dropdown = ttk.Combobox(sector_frame, state="disabled", width=20)
    sector_dropdown.grid(row=0, column=0, sticky="w")

    # Reset Button (X mark)
    reset_button = tk.Button(sector_frame, text="X", font=("Arial", 10), width=2, command=lambda: reset_sector_selection(shared_session, office_dropdown, floor_dropdown, sector_dropdown, desk_dropdown, book_desk_button))
    reset_button.grid(row=0, column=1, padx=(10, 0), sticky="w")


    # Dropdown for desk
    desk_label = tk.Label(dropdowns_frame, text="Select desk:", font=("Arial", 12))
    desk_label.grid(row=6, column=0, padx=10, pady=(10, 5), sticky="w")

    desk_dropdown = ttk.Combobox(dropdowns_frame, state="disabled")
    desk_dropdown.grid(row=7, column=0, padx=10, pady=5, sticky="w")
    desk_dropdown.bind("<<ComboboxSelected>>", lambda event: update_book_desk_button_text(event, desk_dropdown, book_desk_button))


    # Button for booking the desk
    book_desk_button = tk.Button(dropdowns_frame, text=f"Book desk {desk_dropdown.get()}", font=("Arial", 12), state="disabled")
    book_desk_button.grid(row=8, column=0, padx=10, pady=30, sticky="w")
    book_desk_button.bind("<Button-1>", lambda event: print("Desk booked!"))
    book_desk_button.grid_remove()


    # Initially, show the login frame
    all_frames = [login_frame, success_frame]
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