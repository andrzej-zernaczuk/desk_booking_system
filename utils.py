import tkinter as tk
from screeninfo import get_monitors

def show_frame(frame: tk.Frame, all_frames: list[tk.Frame]):
    # Hide all frames
    for f in all_frames:
        f.grid_forget()

    # Show the selected frame
    frame.grid(row=0, column=0, sticky="nsew")

    # Force an update to ensure all widgets are properly displayed
    frame.update_idletasks()


def on_success(frame_to_be_shown: tk.Frame, all_frames: list[tk.Frame]):
    """Callback to transition to the success frame."""
    show_frame(frame_to_be_shown, all_frames)


def center_window(window: tk.Tk):
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
    window.geometry(f'+{x}+{y}')