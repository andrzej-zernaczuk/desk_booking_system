import tkinter as tk
from tkinter import ttk
from utils import show_frame, center_window, on_success
from db.sql_db import create_tables, preload_data, Session
from users_operations.user_login import login


def initialize_app():
    """Initialize the application by setting up the database."""
    print("Initializing the database...")
    create_tables()  # Create tables
    preload_data()   # Preload data


def start_tkinter_app():
    # main window
    root = tk.Tk()
    root.title("Desk Booking Systen by Andrzej Zernaczuk")
    root.resizable(False, True)  # Disable resizing in width
    root.minsize(width=1000, height=400)
    root.after(10, lambda: center_window(root))

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

    # Dropdown lists on the left
    dropdown_office = tk.Label(success_frame, text="Select office:", font=("Arial", 12))
    dropdown_office.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
    dropdown1 = ttk.Combobox(success_frame, values=["Office 1", "Office 2", "Office 3"])
    dropdown1.grid(row=1, column=0, padx=10, pady=5, sticky="w")

    dropdown_floor = tk.Label(success_frame, text="Select office floor:", font=("Arial", 12))
    dropdown_floor.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
    dropdown2 = ttk.Combobox(success_frame, values=["1", "2", "3"])
    dropdown2.grid(row=3, column=0, padx=10, pady=5, sticky="w")

    dropdown_sector = tk.Label(success_frame, text="Select floor sector:", font=("Arial", 12))
    dropdown_sector.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")
    dropdown3 = ttk.Combobox(success_frame, values=["A", "B", "C"])
    dropdown3.grid(row=5, column=0, padx=10, pady=5, sticky="w")

    # Image display on the right
    image_label = tk.Label(success_frame)
    image_label.grid(row=0, column=1, rowspan=6, padx=20, pady=20)

    all_frames = [login_frame, success_frame]

    # Login button
    login_button = tk.Button(login_frame, text="Login", font=("Arial", 12), command=lambda: login(email_entry.get(), password_entry.get(), Session, on_success(success_frame, all_frames)))
    login_button.pack(pady=(20, 0))

    # Initially, show the welcome frame
    show_frame(login_frame, all_frames)

    root.mainloop()

if __name__ == "__main__":
    # Initialize the database
    # initialize_app()

    # Display GUI
    start_tkinter_app()