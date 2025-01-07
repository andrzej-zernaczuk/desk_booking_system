import sys
import logging
import traceback
from csv import reader
from sqlalchemy import Table, select
from db.db_models import Sector, Floor, Office


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


def create_desk_code(desk_data: dict, file_name: str, line: int, sql_session):
    sector_id = desk_data.get("sector_id", None)
    floor_id = desk_data.get("floor_id", None)
    office_id = desk_data.get("office_id", None)

    # check if any of them are missing
    if any([not sector_id, not floor_id, not office_id]):
        raise ValueError(f"Office ID, Floor ID and Sector ID are required for the desks table. Error in CSV {file_name} in line {line}")

    sector_name = sql_session.execute(
        select(Sector.sector_name).where(Sector.sector_id == int(sector_id))
    ).scalar_one_or_none()

    floor_name = sql_session.execute(
        select(Floor.floor_name).where(Floor.floor_id == int(floor_id))
    ).scalar_one_or_none()

    office_name = sql_session.execute(
        select(Office.office_name).where(Office.office_id == int(office_id))
    ).scalar_one_or_none()

    if all([sector_name, floor_name, office_name]):
        desk_data["desk_code"] = f"{office_name}-{floor_name}_{sector_name}_{desk_data['local_id']}"
    else:
        raise ValueError(f"Sector with ID {sector_id} not found in the database.")


def import_table_data(table: Table, file_name: str, field_names: list, sql_session):
    """
    Import rows from csv file into table in database.

    Args:
        table (Table): Table to import data into
        file_name (str): name of csv file
        field_names (list): list of field names
        session (_type_): current session object
    """
    if not if_table_populated(table, sql_session):
        try:
            with open(file_name, "r") as file:
                csv_file = reader(file, skipinitialspace=True)
                header = next(csv_file)

                for line in csv_file:
                    record_data = {field_name: line[i] for i, field_name in enumerate(field_names)}

                    # if desks are being imported generate desk_code for each desk
                    if table.__tablename__ == "desks":
                        create_desk_code(record_data, file_name, csv_file.line_num, sql_session)

                    record = table(**record_data)
                    sql_session.add(record)

            sql_session.commit()
            logging.info(f"Succesfully inserted rows into {table.__tablename__} table")
        except Exception:
            sql_session.rollback()
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback_details = traceback.format_exception(exc_type, exc_value, exc_tb)
            logging.error(f"Error when inserting data into {table.__tablename__} table: {''.join(traceback_details)}")
            raise
        finally:
            sql_session.close()
    else:
        logging.info(f"{table.__tablename__} table is already populated")
