from sqlalchemy.sql import select
from sqlalchemy.orm import Session

from db.db_models import Office, Floor, Sector

def get_available_offices(session_factory):
    """Fetch all available offices."""
    session: Session = session_factory()
    stmt = select(Office.office_name)
    offices = session.execute(stmt).scalars().all()
    session.close()

    return offices


def get_floors_in_office(office_name: str, session_factory):
    """Fetch all floors for a given office."""
    session: Session = session_factory()
    stmt = (
        select(Floor.floor_name)
        .join(Office, Office.office_id == Floor.office_id)
        .where(Office.office_name == office_name)
    )
    floors = session.execute(stmt).scalars().all()
    session.close()

    return floors


def get_sectors_on_floor(floor_name: str, session_factory):
    """Fetch all sectors for a given floor."""
    session: Session = session_factory()
    stmt = (
        select(Sector.sector_name)
        .join(Floor, Floor.floor_id == Sector.floor_id)
        .where(Floor.floor_name == floor_name)
    )
    sectors = session.execute(stmt).scalars().all()
    session.close()

    return sectors