import logging
from typing import Callable, Optional
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from backend_operations.log_utils import log_event

from db.db_models import Office, Floor, Sector, Desk
from db.session_management import managed_session
from backend_operations.user_login import get_current_user


def get_available_offices(session_factory: Callable[[], Session]) -> list[str]:
    """Fetch all available offices.

    :param session_factory: A callable that returns a SQLAlchemy session"""
    try:
        with managed_session(session_factory) as session:
            stmt = select(Office.office_name)
            offices = session.execute(stmt).scalars().all()
        return offices
    except Exception as exc:
        logging.error(f"Error fetching available offices: {exc}")
        log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching available offices: {exc}")
        return []


def get_floors_in_office(session_factory: Callable[[], Session], office_name: str) -> list[str]:
    """Fetch all floors for a given office.

    :param session_factory: A callable that returns a SQLAlchemy session
    :param office_name: The office name"""
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
        log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching available office floors: {exc}")
        return []


def get_sectors_on_floor(session_factory: Callable[[], Session], floor_name: str) -> list[str]:
    """Fetch all sectors for a given floor.

    :param session_factory: A callable that returns a SQLAlchemy session
    :param floor_name: The floor name"""
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
        log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching available floor sectors: {exc}")
        return []


def get_desks_on_floor(session_factory: Callable[[], Session], floor_name: str, sector_name: Optional[str]) -> list[str]:
    """Fetch desks for a specific floor.

    :param session_factory: A callable that returns a SQLAlchemy session
    :param floor_name: The floor name"""
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
        log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching available desks: {exc}")
        return []


def get_desk_sector(session_factory: Callable[[], Session], desk_code: str) -> str:
    """Fetch the sector for a given desk.

    :param session_factory: A callable that returns a SQLAlchemy session
    :param desk_code: The desk code
    """
    try:
        with managed_session(session_factory) as session:
            stmt = (
                select(Sector.sector_name)
                .join(Desk, Desk.sector_id == Sector.sector_id)
                .where(Desk.desk_code == desk_code)
            )
            sector = session.execute(stmt).scalar_one()
        return sector
    except Exception as exc:
        logging.error(f"Error fetching sector for desk '{desk_code}': {exc}")
        log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching desk sector: {exc}")
        return None