import logging

from db.sql_db import SessionFactory


def initialize_shared_session():
    """Ensure the shared session is initialized."""
    try:
        session = SessionFactory()
        logging.info("Shared session initialized successfully.")
        return session
    except Exception as exc:
        logging.error(f"Failed to initialize shared session: {exc}")
        return None


def close_shared_session(session_for_closing):
    """Close the provided session when the app exits."""
    try:
        if session_for_closing:
            session_for_closing.close()
            logging.info("Shared session closed successfully.")
    except Exception as exc:
        logging.error(f"Failed to close shared session: {exc}")
