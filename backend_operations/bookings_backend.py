import logging
from typing import Callable, Optional
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from backend_operations.log_utils import log_event

from db.db_models import Office, Floor, Sector, Desk
from db.session_management import managed_session
from backend_operations.user_login import get_current_user


# def create_booking(session_factory: Callable[[], Session], desk_code: str) -> list[str]:
#     """Create Booking.

#     :param session_factory: A callable that returns a SQLAlchemy session
#     :param floor_name: The floor name"""
#     try:
#         with managed_session(session_factory) as session:
#             stmt = (
#                 select(Sector.sector_name)
#                 .join(Floor, Floor.floor_id == Sector.floor_id)
#                 .where(Floor.floor_name == floor_name)
#             )
#             sectors = session.execute(stmt).scalars().all()
#         return sectors
#     except Exception as exc:
#         logging.error(f"Error fetching sectors for floor '{floor_name}': {exc}")
#         log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching available floor sectors: {exc}")
#         return []


# def get_desk_info(session_factory: Callable[[], Session], desk_code: str) -> list[str]:
#     """Fetch desk information.

#     :param session_factory: A callable that returns a SQLAlchemy session
#     :param desk_code: The desk code"""
#     try:
#         with managed_session(session_factory) as session:
#             stmt = (
#                 select(Desk.desk_code, Desk.desk_name, Desk.desk_status)
#                 .where(Desk.desk_code == desk_code)
#             )
#             desk_info = session.execute(stmt).scalars().all()
#         return desk_info
#     except Exception as exc:
#         logging.error(f"Error fetching desk information for desk '{desk_code}': {exc}")
#         log_event(get_current_user(), "Failure", "Desk selection", f"Exception occured while fetching desk information: {exc}")
#         return []