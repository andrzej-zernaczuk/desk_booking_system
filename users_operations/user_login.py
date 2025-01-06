import bcrypt
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.db_models import User


def login(email: str, password: str, session_factory, on_success_callback):
    """
    Handles the login process.

    :param email: The user's email address
    :param password: The user's password
    :param session_factory: A callable to create a SQLAlchemy session (e.g., `scoped_session`)
    :param on_success: A callback function to execute on successful login
    """
    if not email or not password:
        messagebox.showerror("Login Error", "Both email and password are required.")
        return

    # Create a database session
    session: Session = session_factory()

    try:
        # Use session.execute() with a select statement
        stmt = select(User).where(User.email == email)
        result = session.execute(stmt)
        user = result.scalar_one_or_none()  # Get a single result or None if not found

        if not user:
            messagebox.showerror("Login Error", "Invalid email or password.")
            return

        # Verify the password
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            on_success_callback
        else:
            messagebox.showerror("Login Error", "Invalid email or password.")
    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
    finally:
        session.close()
