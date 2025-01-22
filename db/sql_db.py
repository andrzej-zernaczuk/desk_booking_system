import sys
import logging
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from google.cloud.sql.connector import Connector

from db.csv_import import import_table_data
from backend_operations.utils import get_time_change
from db.db_models import Role, Department, Status, Office, Floor, Sector, Desk, Base
from backend_operations.utils import (
    load_environment_variables,
    get_env_variable,
    resource_path,
)


# Load environment variables at the start
load_environment_variables()

# Access specific variables
USE_PUBLIC_IP = get_env_variable("USE_PUBLIC_IP") == "True"
SQL_USERNAME = get_env_variable("sql_username")
SQL_PASSWORD = get_env_variable("sql_password")
SQL_DATABASE = get_env_variable("sql_database")


def getconn():
    """Returns a database connection for both Public IP and Cloud SQL Connector cases."""
    try:
        from pg8000 import connect  # Ensure pg8000 is imported

        if USE_PUBLIC_IP:
            PUBLIC_IP = get_env_variable("PUBLIC_IP")
            # Public IP connection
            return connect(
                host=PUBLIC_IP,
                user=SQL_USERNAME,
                password=SQL_PASSWORD,
                database=SQL_DATABASE,
            )
        else:
            INSTANCE_CONNECTION_NAME = get_env_variable("INSTANCE_CONNECTION_NAME")
            connector = Connector()
            # Google Cloud SQL Connector connection
            return connector.connect(
                str(INSTANCE_CONNECTION_NAME),
                "pg8000",
                user=SQL_USERNAME,
                password=SQL_PASSWORD,
                db=SQL_DATABASE,
            )
    except Exception as e:
        raise RuntimeError(f"Error connecting to database: {e}")


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
        sys.exit()


def preload_data():
    """Preloads data into the database from CSV files."""
    try:
        session_import: Session = SessionFactory()
        import_table_data(session_import, Role, resource_path("db/data/roles.csv"), ["role_name"])
        import_table_data(session_import, Department, resource_path("db/data/departments.csv"), ["department_name"])
        import_table_data(session_import, Status, resource_path("db/data/statuses.csv"), ["status_name"])
        import_table_data(session_import, Office, resource_path("db/data/offices.csv"), ["office_name"])
        import_table_data(session_import, Floor, resource_path("db/data/floors.csv"), ["office_id", "floor_name"])
        import_table_data(session_import, Sector, resource_path("db/data/sectors.csv"), ["floor_id", "sector_name"])
        import_table_data(
            session_import,
            Desk,
            resource_path("db/data/desks.csv"),
            ["office_id", "floor_id", "sector_id", "local_id"],
        )
        session_import.commit()
        logging.info("Data is ready.")
    except ValueError as val_err:
        logging.error(f"Error while preloading data: {val_err}")
        session_import.rollback()
        sys.exit()
    except Exception as error:
        logging.error(f"Error while preloading data: {error}")
        session_import.rollback()
        sys.exit()
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
                sys.exit()
    except Exception as exc:
        logging.error(f"Error while creating trigger for overlapping bookings: {exc}")
        sys.exit()


def initialize_pg_cron(engine):
    """Initialize the scheduled booking status updates using pg_cron."""
    try:
        # Check if pg_cron extension is installed
        with engine.connect() as connection:
            # Begin transaction
            pg_cron_transaction = connection.begin()

            try:
                result = connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'pg_cron';
                        """
                    )
                ).scalar()

                if not result:
                    logging.error("pg_cron extension is not installed. Please install it to use this feature.")
                    sys.exit()

                # Get current time offset from UTC for Poland
                time_change = get_time_change()
                # Create the function to update booking statuses
                connection.execute(
                    sqlalchemy.text(
                        f"""
                        CREATE OR REPLACE FUNCTION update_booking_statuses()
                        RETURNS void LANGUAGE plpgsql AS $$
                        BEGIN
                            -- Cancel bookings that were not checked in within 30 minutes of the start time
                            UPDATE bookings
                            SET status_id = (SELECT status_id FROM statuses WHERE status_name = 'Canceled')
                            WHERE status_id = (SELECT status_id FROM statuses WHERE status_name = 'Pending')
                            AND (start_date + INTERVAL '30 minutes') < (NOW() + INTERVAL '{time_change} hour');

                            -- Cancel bookings if the end time has passed and they are still pending
                            UPDATE bookings
                            SET status_id = (SELECT status_id FROM statuses WHERE status_name = 'Canceled')
                            WHERE status_id = (SELECT status_id FROM statuses WHERE status_name = 'Pending')
                            AND end_date < (NOW() + INTERVAL '{time_change} hour');

                            -- Complete bookings whose end time has passed
                            UPDATE bookings
                            SET status_id = (SELECT status_id FROM statuses WHERE status_name = 'Completed')
                            WHERE status_id = (SELECT status_id FROM statuses WHERE status_name = 'Active')
                            AND end_date < (NOW() + INTERVAL '{time_change} hour');
                        END;
                        $$;
                        """
                    )
                )

                # Schedule the function to run every minute
                connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT cron.schedule('update_booking_statuses', '*/1 * * * *', 'SELECT update_booking_statuses();');
                        """
                    )
                )
                pg_cron_transaction.commit()
                logging.info("Cron job for booking status updates created successfully.")
            except Exception as exc:
                pg_cron_transaction.rollback()
                logging.error(f"Error while creating cron job for booking status updates: {exc}")
                sys.exit()
    except:
        logging.error("Error while initializing pg_cron.")
        sys.exit()


# PROJECT REQUIREMENT: views
def create_most_frequent_users_view(engine):
    """
    Create the most_frequent_users view in the database.
    This view calculates the user with the most reservations and their reservation count.

    :param engine: SQLAlchemy engine connected to the database.
    """
    try:
        with engine.connect() as connection:
            # Begin transaction
            transaction = connection.begin()

            try:
                connection.execute(sqlalchemy.text("DROP VIEW IF EXISTS most_frequent_users;"))
                connection.execute(
                    sqlalchemy.text(
                        """
                        CREATE OR REPLACE VIEW most_frequent_users AS
                        SELECT
                            users.user_name,
                            COUNT(bookings.booking_id) AS reservation_count
                        FROM
                            users
                        JOIN
                            bookings ON users.user_name = bookings.user_name
                        GROUP BY
                            users.user_name
                        ORDER BY
                            reservation_count DESC;
                        """
                    )
                )

                transaction.commit()
                logging.info("View 'most_frequent_users' created successfully.")
            except Exception as exc:
                transaction.rollback()
                logging.error(f"Error while creating 'most_frequent_users' view: {exc}")
                raise
    except Exception as exc:
        logging.error(f"Failed to create view 'most_frequent_users': {exc}")
        raise


def initialize_app_db():
    """Initialize the application by setting up the database."""
    try:
        create_tables()
        preload_data()
        create_trigger(desk_booking_engine)
        initialize_pg_cron(desk_booking_engine)
        create_most_frequent_users_view(desk_booking_engine)
    except (Exception, ValueError) as error:
        logging.error(f"Error during database initialization: {error}")
        raise
