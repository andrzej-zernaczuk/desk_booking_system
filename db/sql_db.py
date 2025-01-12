import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from google.cloud.sql.connector import Connector

from db.db_models import Base, Role, Department, Status, Office, Floor, Sector, Desk
from db.csv_import import import_table_data

# Load environment variables
load_dotenv("../.env")

# Initialize Connector object
connector = Connector()

def getconn():
    """Returns a database connection using Google Cloud SQL Connector."""
    return connector.connect(
        os.getenv("INSTANCE_CONNECTION_NAME"),
        "pg8000",
        user=os.getenv("sql_username"),
        password=os.getenv("sql_password"),
        db=os.getenv("sql_database"),
    )

def init_engine():
    """Initializes the SQLAlchemy engine with a connection pool."""
    return create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=0,
    )

# Initialize the engine and session factory
desk_booking_engine = init_engine()

SessionFactory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=desk_booking_engine))

def create_tables():
    """Creates all tables defined in the ORM models."""
    try:
        Base.metadata.create_all(bind=desk_booking_engine)
        logging.info("Database tables are ready.")
    except Exception as error:
        logging.error(f"Error while creating tables: {error}")
        exit()


def preload_data():
    """Preloads data into the database from CSV files."""
    try:
        session_import: Session = SessionFactory()
        import_table_data(Role, "db/data/roles.csv", ["role_name"], session_import)
        import_table_data(Department, "db/data/departments.csv", ["department_name"], session_import)
        import_table_data(Status, "db/data/statuses.csv", ["status_name"], session_import)
        import_table_data(Office, "db/data/offices.csv", ["office_name"], session_import)
        import_table_data(Floor, "db/data/floors.csv", ["office_id", "floor_name"], session_import)
        import_table_data(Sector, "db/data/sectors.csv", ["floor_id", "sector_name"], session_import)
        import_table_data(Desk, "db/data/desks.csv", ["office_id", "floor_id", "sector_id", "local_id"], session_import)
        session_import.commit()
        logging.info("Data is ready.")
    except Exception as error:
        logging.error(f"Error while preloading data: {error}")
        session_import.rollback()
        exit()
    except ValueError as val_err:
        logging.error(f"Error while preloading data: {val_err}")
        session_import.rollback()
        exit()
    finally:
        session_import.close()


def initialize_app_db():
    """Initialize the application by setting up the database."""
    try:
        create_tables()  # Create tables
        preload_data()   # Preload data
    except (Exception, ValueError) as error:
        logging.error(f"Error during database initialization: {error}")
        raise