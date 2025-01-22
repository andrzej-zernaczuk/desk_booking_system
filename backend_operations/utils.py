import os
import sys
import pytz
import base64
from datetime import datetime
from dotenv import load_dotenv


def get_time_change():
    try:
        # Define the Poland timezone
        poland_tz = pytz.timezone("Europe/Warsaw")

        # Get the current time in UTC and convert it to Poland timezone
        now_utc = datetime.now(pytz.utc)  # Get current time in UTC with timezone info
        now_poland = now_utc.astimezone(poland_tz)  # Convert to Poland timezone

        # Calculate the time offset in hours from UTC
        offset = now_poland.utcoffset()
        if offset is not None:
            return int(offset.total_seconds() / 3600)  # Return the offset in hours
        else:
            raise ValueError("Could not calculate UTC offset for Europe/Warsaw.")
    except Exception as e:
        raise ValueError(f"Error in get_time_change: {e}")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # For PyInstaller
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

        # If debugging (not using PyInstaller), ensure base_path is the project root
        if not getattr(sys, "_MEIPASS", False):  # Check if running as packaged
            base_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )  # Move up one level to project root

        return os.path.join(base_path, relative_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to resolve resource path for {relative_path}. Error: {exc}")


def get_env_variable(var_name: str, default_value=None):
    """Get an environment variable, or raise an exception if it is missing."""
    load_environment_variables()
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' is not set and has no default value.")
    return value


def load_environment_variables():
    """
    Load environment variables from a Base64-encoded `.env` file.
    """
    b64_env_path = resource_path("env.b64")
    if not os.path.exists(b64_env_path):
        raise FileNotFoundError("The Base64-encoded .env file is missing.")

    # Decode the Base64-encoded .env file
    with open(b64_env_path, "r") as b64_file:
        decoded_env = base64.b64decode(b64_file.read()).decode("utf-8")

    # Save the decoded .env file to a temporary location
    temp_env_path = "/tmp/embedded_env"
    with open(temp_env_path, "w") as temp_env_file:
        temp_env_file.write(decoded_env)

    # Load the environment variables and clean up
    load_dotenv(temp_env_path)
    os.remove(temp_env_path)
