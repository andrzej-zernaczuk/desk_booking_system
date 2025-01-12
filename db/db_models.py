from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import (
    declarative_base,
    relationship
)
from sqlalchemy.sql import func

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String, unique=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="department")

    def __repr__(self):
        return (f"<Department(department_id={self.department_id}, "
                f"department_name='{self.department_name}')>")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return (f"<User(user_id={self.user_id}, user_name='{self.user_name}', "
                f"role_id={self.role_id}, department_id={self.department_id})>")


class Office(Base):
    __tablename__ = "offices"

    office_id = Column(Integer, primary_key=True, autoincrement=True)
    office_name = Column(String, nullable=False, unique=True)

    # Relationships
    floors = relationship("Floor", back_populates="office")
    desks = relationship("Desk", back_populates="office")

    def __repr__(self):
        return f"<Office(office_id={self.office_id}, office_name='{self.office_name}')>"


class Floor(Base):
    __tablename__ = "floors"

    floor_id = Column(Integer, primary_key=True, autoincrement=True)
    office_id = Column(Integer, ForeignKey("offices.office_id"), nullable=False)
    floor_name = Column(String, nullable=False)

    # Relationships
    office = relationship("Office", back_populates="floors")
    sectors = relationship("Sector", back_populates="floor")
    desks = relationship("Desk", back_populates="floor")

    def __repr__(self):
        return (f"<Floor(floor_id={self.floor_id}, floor_name='{self.floor_name}', "
                f"office_id={self.office_id})>")

class Sector(Base):
    __tablename__ = "sectors"

    sector_id = Column(Integer, primary_key=True, autoincrement=True)
    floor_id = Column(Integer, ForeignKey("floors.floor_id"), nullable=False)
    sector_name = Column(String, nullable=False)

    # Composite unique constraint: sector_name + floor_id
    __table_args__ = (
        UniqueConstraint("floor_id", "sector_name", name="uq_floor_sector_name"),
    )

    # Relationships
    floor = relationship("Floor", back_populates="sectors")
    desks = relationship("Desk", back_populates="sector")

    def __repr__(self):
        return (f"<Sector(sector_id={self.sector_id}, sector_name='{self.sector_name}', "
                f"floor_id={self.floor_id})>")

class Desk(Base):
    __tablename__ = "desks"

    desk_id = Column(Integer, primary_key=True, autoincrement=True)
    office_id = Column(Integer, ForeignKey("offices.office_id"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.floor_id"), nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.sector_id"), nullable=False)
    local_id = Column(Integer, nullable=False)
    desk_code = Column(String, unique=True, nullable=False)
    description = Column(String)

    # Relationships
    office = relationship("Office", back_populates="desks")
    floor = relationship("Floor", back_populates="desks")
    sector = relationship("Sector", back_populates="desks")
    bookings = relationship("Booking", back_populates="desk")

    def __repr__(self):
        return (f"<Desk(desk_id={self.desk_id}, desk_code='{self.desk_code}', "
                f"office_id={self.office_id}, floor_id={self.floor_id}, "
                f"sector_id={self.sector_id}, local_id={self.local_id})>")


class Status(Base):
    __tablename__ = "statuses"

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String, unique=True, nullable=False)

    # Relationships
    bookings = relationship("Booking", back_populates="status")

    def __repr__(self):
        return (f"<Status(status_id={self.status_id}, "
                f"status_name='{self.status_name}')>")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, ForeignKey("users.user_name"), nullable=False)
    desk_code = Column(String, ForeignKey("desks.desk_code"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status_id = Column(Integer, ForeignKey("statuses.status_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="bookings")
    desk = relationship("Desk", back_populates="bookings")
    status = relationship("Status", back_populates="bookings")

    def __repr__(self):
        return (f"<Booking(booking_id={self.booking_id}, user_name={self.user_name}, "
                f"desk_code='{self.desk_code}', status_id={self.status_id}, "
                f"start_date={self.start_date}, end_date={self.end_date})>")


class Log(Base):
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    component = Column(String, nullable=False)
    event_description = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return (f"<Log(log_id={self.log_id}, user_name={self.user_name}, "
                f"event_type='{self.event_type}', event_description='{self.event_description}', created_at={self.created_at})>")
