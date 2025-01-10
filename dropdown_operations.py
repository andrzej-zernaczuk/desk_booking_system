import logging
from typing import Callable, Generator, Optional
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from contextlib import contextmanager

from db.db_models import Office, Floor, Sector, Desk

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
        raise
    finally:
        if 'session' in locals() and session is not None:
            session.close()


def get_available_offices(session_factory: Callable[[], Session]) -> list[str]:
    """Fetch all available offices."""
    try:
        with managed_session(session_factory) as session:
            stmt = select(Office.office_name)
            offices = session.execute(stmt).scalars().all()
        return offices
    except Exception as exc:
        logging.error(f"Error fetching available offices: {exc}")
        return []


def get_floors_in_office(office_name: str, session_factory: Callable[[], Session]) -> list[str]:
    """Fetch all floors for a given office."""
    try:
        with managed_session(session_factory) as session:
            stmt = (
                select(Floor.floor_name)
                .join(Office, Office.office_id == Floor.office_id)
                .where(Office.office_name == office_name)
            )
            floors = session.execute(stmt).scalars().all()
        return floors
    except Exception as exc:
        logging.error(f"Error fetching floors for office '{office_name}': {exc}")
        return []


def get_sectors_on_floor(floor_name: str, session_factory: Callable[[], Session]) -> list[str]:
    """Fetch all sectors for a given floor."""
    try:
        with managed_session(session_factory) as session:
            stmt = (
                select(Sector.sector_name)
                .join(Floor, Floor.floor_id == Sector.floor_id)
                .where(Floor.floor_name == floor_name)
            )
            sectors = session.execute(stmt).scalars().all()
        return sectors
    except Exception as exc:
        logging.error(f"Error fetching sectors for floor '{floor_name}': {exc}")
        return []


def get_desks_on_floor(floor_name: str, sector_name: Optional[str], session_factory):
    """Fetch desks for a specific floor."""
    try:
        with managed_session(session_factory) as session:
            stmt = (
                select(Desk.desk_code)
                .join(Floor, Floor.floor_id == Desk.floor_id)
                .where(Floor.floor_name == floor_name)
            )

            # If sector_name is provided, add a filter for the sector
            if sector_name:
                stmt = (
                    stmt.join(Sector, Sector.sector_id == Desk.sector_id)
                    .where(Sector.sector_name == sector_name)
                )

            desks = session.execute(stmt).scalars().all()
        return desks
    except Exception as exc:
        logging.error(f"Error fetching desks for floor '{floor_name}' and sector '{sector_name}': {exc}")
        return []