import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from google.cloud.sql.connector import Connector

from db.db_models import Base, Role, Department, Status
from db.csv_import import import_simple_data_structure

# Load environment variables
load_dotenv("./app/.env")

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
Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=desk_booking_engine))

def create_tables():
    """Creates all tables defined in the ORM models."""
    Base.metadata.create_all(bind=desk_booking_engine)
    logging.info("Database tables created successfully.")

def preload_data():
    """Preloads data into the database from CSV files."""
    try:
        session_import = Session()
        import_simple_data_structure(Role, "db/data/roles.csv", "role_name", session_import)
        import_simple_data_structure(Department, "db/data/departments.csv", "department_name", session_import)
        import_simple_data_structure(Status, "db/data/statuses.csv", "status_name", session_import)
        session_import.commit()
        logging.info("Data preloaded successfully.")
    except Exception as error:
        logging.error(f"Error while preloading data: {error}")
        session_import.rollback()
    finally:
        session_import.close()

# Initialize the database (tables and optional preloading)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    create_tables()
    preload_data()
