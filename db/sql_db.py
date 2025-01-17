import os
import logging
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from google.cloud.sql.connector import Connector

from db.csv_import import import_table_data
from db.db_models import Base, Role, Department, Status, Office, Floor, Sector, Desk

# Load environment variables
load_dotenv("../.env")

# Initialize Connector object
connector = Connector()


def getconn() -> sqlalchemy.engine.base.Connection:
    """Returns a database connection using Google Cloud SQL Connector."""
    return connector.connect(
        str(os.getenv("INSTANCE_CONNECTION_NAME")),
        "pg8000",
        user=os.getenv("sql_username"),
        password=os.getenv("sql_password"),
        db=os.getenv("sql_database"),
    )


def init_engine() -> sqlalchemy.engine.base.Engine:
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
        import_table_data(session_import, Role, "db/data/roles.csv", ["role_name"])
        import_table_data(session_import, Department, "db/data/departments.csv", ["department_name"])
        import_table_data(session_import, Status, "db/data/statuses.csv", ["status_name"])
        import_table_data(session_import, Office, "db/data/offices.csv", ["office_name"])
        import_table_data(session_import, Floor, "db/data/floors.csv", ["office_id", "floor_name"])
        import_table_data(session_import, Sector, "db/data/sectors.csv", ["floor_id", "sector_name"])
        import_table_data(
            session_import, Desk, "db/data/desks.csv", ["office_id", "floor_id", "sector_id", "local_id"]
        )
        session_import.commit()
        logging.info("Data is ready.")
    except ValueError as val_err:
        logging.error(f"Error while preloading data: {val_err}")
        session_import.rollback()
        exit()
    except Exception as error:
        logging.error(f"Error while preloading data: {error}")
        session_import.rollback()
        exit()
    finally:
        session_import.close()


# PROJECT REQUIREMENT: triggers
def create_trigger(engine):
    """Create a trigger to prevent overlapping bookings."""
    try:
        with engine.connect() as connection:
            # Begin transaction
            trig_transaction = connection.begin()

            try:
                # Check if the trigger already exists
                result = connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT 1
                        FROM pg_trigger
                        WHERE tgname = 'prevent_overlapping_bookings_trigger';
                    """
                    )
                ).scalar()

                if result:
                    logging.info("Trigger 'prevent_overlapping_bookings_trigger' already exists. Skipping creation.")
                    return

                # Create the function
                connection.execute(
                    sqlalchemy.text(
                        """
                        CREATE OR REPLACE FUNCTION prevent_overlapping_bookings()
                        RETURNS TRIGGER AS $$
                        BEGIN
                            -- Bypass check if only status_id or other unrelated fields are being updated
                            IF TG_OP = 'UPDATE' AND
                            NEW.start_date = OLD.start_date AND
                            NEW.end_date = OLD.end_date AND
                            NEW.user_name = OLD.user_name THEN
                                RETURN NEW;
                            END IF;

                            -- Check if the user has an overlapping booking, ignoring cancelled bookings (status_id = 4)
                            IF EXISTS (
                                SELECT 1
                                FROM bookings
                                WHERE NEW.user_name = bookings.user_name
                                AND NEW.start_date < bookings.end_date
                                AND NEW.end_date > bookings.start_date
                                AND (NEW.booking_id IS NULL OR NEW.booking_id <> bookings.booking_id) -- Exclude self
                                AND bookings.status_id <> 4 -- Ignore cancelled bookings
                            ) THEN
                                RAISE EXCEPTION 'Overlapping booking detected for user %', NEW.user_name;
                            END IF;

                            RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;
                        """
                    )
                )

                # Create the trigger
                connection.execute(
                    sqlalchemy.text(
                        """
                        CREATE TRIGGER prevent_overlapping_bookings_trigger
                        BEFORE INSERT OR UPDATE ON bookings
                        FOR EACH ROW
                        EXECUTE FUNCTION prevent_overlapping_bookings();
                    """
                    )
                )

                trig_transaction.commit()
                logging.info("Trigger for preventing overlapping bookings created successfully.")
            except Exception as exc:
                trig_transaction.rollback()
                logging.error(f"Error while creating trigger for overlapping bookings: {exc}")
                exit()
    except Exception as exc:
        logging.error(f"Error while creating trigger for overlapping bookings: {exc}")
        exit()


def initialize_app_db():
    """Initialize the application by setting up the database."""
    try:
        create_tables()  # Create tables
        preload_data()  # Preload data
        create_trigger(desk_booking_engine)  # Create trigger
    except (Exception, ValueError) as error:
        logging.error(f"Error during database initialization: {error}")
        raise
