import logging
from sqlalchemy.orm import Session
from contextlib import contextmanager
from typing import Callable, Generator

from db.sql_db import SessionFactory
from backend_operations.log_utils import log_event
from backend_operations.user_login import get_current_user


@contextmanager
def managed_session(session_factory: Callable[[], Session]) -> Generator[Session, None, None]:
    """
    A context manager for managing SQLAlchemy sessions.

    :param session_factory: A callable that returns a SQLAlchemy session
    :yield: A SQLAlchemy session
    """
    try:
        session = session_factory()
        if session is None:
            raise RuntimeError("Session factory returned None. Ensure session is properly initialized.")
        yield session
    except Exception as exc:
        logging.error(f"Session error: {exc}")
        log_event(get_current_user(), "Failure", "DB connection", f"Exception occured while creating managed session: {exc}")
        raise
    finally:
        if 'session' in locals() and session is not None:
            session.close()



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
