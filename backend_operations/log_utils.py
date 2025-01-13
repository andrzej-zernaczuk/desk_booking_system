import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from db.db_models import Log
from db.sql_db import SessionFactory


def log_event(user_email: str, event_type: str, component: str, event_description: str) -> None:
    """
    Logs an event in the logs table.

    :param user_email: ID (email) of the user associated with the event
    :param event_type: Type of the event (e.g., "Login Success", "Login Failure")
    :param session_factory: A callable to create a SQLAlchemy session
    """
    session: Session = SessionFactory()

    try:
        log_entry = Log(
            user_name=user_email,
            event_type=event_type,
            component=component,
            event_description=event_description,
        )
        session.add(log_entry)
        session.commit()
        logging.info(f"[{user_email}] Logged event: {event_description}.")
    except Exception as exc:
        session.rollback()
        logging.error(f"Failed to log event: {exc}")
    finally:
        session.close()
