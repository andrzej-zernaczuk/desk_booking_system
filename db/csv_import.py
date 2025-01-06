import sys
import logging
import traceback
from csv import reader
from sqlalchemy import Table

from db.db_models import Role, Department, Status

def if_table_populated(table: Table, sql_session) -> bool:
    """
    Check if table has rows.

    Args:
        table (Table): Table to check
        session (_type_): current session object

    Returns:
        bool
    """
    if sql_session.query(table).count() > 0:
        return True
    else:
        False

def import_simple_data_structure(table: Table, file_name: str, field_name: str, sql_session):
    """
    Import rows from csv file into table in database.

    Args:
        table (Table): Table to import data into
        file_name (str): name of csv file
        session (_type_): current session object
    """
    if not if_table_populated(table, sql_session):
        try:
            with open(file_name, "r") as file:
                csv_file = reader(file, skipinitialspace=True)
                header = next(csv_file)

                for line in csv_file:
                    record = table(**{f"{field_name}": line[0]})
                    sql_session.add(record)

                sql_session.commit()
                logging.info(f"Succesfully inserted rows into {table.__tablename__} table")
        except Exception:
            sql_session.rollback()
            logging.error(f"Error when inserting data into {table.__tablename__} table.")
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback_details = traceback.format_exception(exc_type, exc_value, exc_tb)
            logging.error(f"Exception occurred: {''.join(traceback_details)}")
        finally:
            sql_session.close()
    else:
        logging.info(f"{table.__tablename__} table is already populated")