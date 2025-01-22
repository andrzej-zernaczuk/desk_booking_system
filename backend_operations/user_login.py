import sys
import bcrypt
import logging
from typing import Callable
from tkinter import messagebox
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.db_models import User
from db.sql_db import SessionFactory
from backend_operations.log_utils import log_event
from backend_operations.utils import get_env_variable


# Initialize global variable storing logged-in user ID
CURRENT_USER = None


def login(email: str, password: str, on_success_callback: Callable[[], None]) -> None:
    """
    Handles the login process.

    :param email: The user's email address
    :param password: The user's password
    :param session_factory: A callable to create a SQLAlchemy session (e.g., `scoped_session`)
    :param on_success: A callback function to execute on successful login
    """

    if check_debug_mode():
        debug_user = get_debug_user()
        set_current_user(debug_user)
        logging.info(f"Debug mode is enabled, login is skipped, user set to: '{get_current_user()}'.")
        log_event("SYSTEM", "Success", "Login", f"Debug mode is enabled, login is skipped")
        on_success_callback()
        return

    if not email or not password:
        messagebox.showerror("Login Error", "Both email and password are required.")
        return

    # Create a database session
    session: Session = SessionFactory()

    try:
        stmt = select(User).where(User.user_name == email)
        result = session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logging.error(f"User with email {email} not found.")
            log_event("SYSTEM", "Failure", "Login", f"Invalid email: {email} used for logging in")
            messagebox.showerror("Login Error", "Invalid email or password.")
            return

        # Verify the password
        if bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            set_current_user(email)
            logging.info(f"User with email {email} logged in successfully.")
            log_event(get_current_user(), "Success", "Login", f"Successful login")

            on_success_callback()
        else:
            logging.error(f"Invalid password for user with email {email}.")
            log_event(email, "Failure", "Login", f"Invalid password")
            messagebox.showerror("Login Error", "Invalid email or password.")
    except Exception as exc:
        logging.error(f"An error occurred: {exc}")
        log_event(get_current_user(), "Failure", "Login", f"An error occurred: {exc}")
        messagebox.showerror("Database Error", f"Database error. Please contact the administrator.")
    finally:
        session.close()


def check_debug_mode() -> bool:
    """Check if the debug mode is enabled."""
    is_debug_mode = get_env_variable("debug_mode")
    return is_debug_mode == "True"


def get_debug_user() -> str:
    """Return the debug user."""
    debug_acc = get_env_variable("debug_account")
    if not debug_acc:
        raise ValueError("Debug account is not set in the .env file.")

    return debug_acc


def get_current_user() -> str:
    """Return the current user."""
    if not CURRENT_USER:
        logging.error("CURRENT_USER is not set. Critical error.")
        sys.exit()

    return CURRENT_USER


def set_current_user(user_email: str) -> None:
    """
    Set the current user.

    :param user_email: The user ID to set
    """
    global CURRENT_USER
    if CURRENT_USER is None:
        CURRENT_USER = user_email
    else:
        raise ValueError("CURRENT_USER is already set and cannot be changed.")
