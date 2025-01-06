from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Date,
    ForeignKey
)
from sqlalchemy.orm import (
    declarative_base,
    relationship
)
from datetime import datetime, timezone

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False)

    # Relationship to "User"
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String, unique=True, nullable=False)

    # Relationship to "User"
    users = relationship("User", back_populates="department")

    def __repr__(self):
        return (f"<Department(department_id={self.department_id}, "
                f"department_name='{self.department_name}')>")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=False)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    bookings = relationship("Booking", back_populates="user")
    logs = relationship("Log", back_populates="user")

    def __repr__(self):
        return (f"<User(user_id={self.user_id}, username='{self.username}', "
                f"email='{self.email}', role_id={self.role_id}, "
                f"department_id={self.department_id})>")


class Desk(Base):
    __tablename__ = "desks"

    desk_id = Column(Integer, primary_key=True, autoincrement=True)
    office = Column(String, nullable=False)
    floor = Column(Integer, nullable=False)
    sector = Column(String, nullable=False)
    local_id = Column(Integer, nullable=False)
    desk_code = Column(String, unique=True, nullable=False)
    description = Column(String)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship to "Booking"
    bookings = relationship("Booking", back_populates="desk")

    def __repr__(self):
        return (f"<Desk(desk_id={self.desk_id}, desk_code='{self.desk_code}', "
                f"office='{self.office}', floor={self.floor}, "
                f"sector='{self.sector}')>")


class Status(Base):
    __tablename__ = "statuses"

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String, unique=True, nullable=False)

    # Relationship to "Booking"
    bookings = relationship("Booking", back_populates="status")

    def __repr__(self):
        return (f"<Status(status_id={self.status_id}, "
                f"status_name='{self.status_name}')>")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    desk_code = Column(String, ForeignKey("desks.desk_code"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status_id = Column(Integer, ForeignKey("statuses.status_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="bookings")
    desk = relationship("Desk", back_populates="bookings")
    status = relationship("Status", back_populates="bookings")

    def __repr__(self):
        return (f"<Booking(booking_id={self.booking_id}, user_id={self.user_id}, "
                f"desk_code='{self.desk_code}', status_id={self.status_id}, "
                f"start_date={self.start_date}, end_date={self.end_date})>")


class Log(Base):
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship to "User"
    user = relationship("User", back_populates="logs")

    def __repr__(self):
        return (f"<Log(log_id={self.log_id}, user_id={self.user_id}, "
                f"action='{self.action}', created_at={self.created_at})>")
