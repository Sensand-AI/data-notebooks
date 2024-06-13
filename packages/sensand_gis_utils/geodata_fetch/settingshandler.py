# Settings reader and handler
"""
Functions for reading and handling the input 'settings.json' file that specifies the data to collect.
"""

import datetime
import json
from types import SimpleNamespace


def DateEncoder(obj):
    """
    JSON encoder for datetime objects.

    Args:
        obj (datetime.datetime or datetime.date): The datetime object to be encoded.

    Returns:
        str: The encoded datetime string in the format '%Y-%m-%d'.
    """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.strftime("%Y-%m-%d")


def display_settings(fname_settings):
    """
    Display the settings stored in a JSON file.

    Args:
        fname_settings (str): The path to the JSON file containing the settings.

    Returns:
        None
    """
    with open(fname_settings, "r") as f:
        settings = json.load(f)
        print(json.dumps(settings, indent=4, sort_keys=True, default=DateEncoder))


def main(fname_settings, to_namespace=True):
    """
    Load and process settings from a JSON file.

    Args:
        fname_settings (str): The path to the JSON file containing the settings.
        to_namespace (bool, optional): Whether to convert the settings dictionary to a namespace.
            Defaults to True.

    Returns:
        settings (dict or SimpleNamespace): The processed settings.

    Raises:
        FileNotFoundError: If the specified JSON file does not exist.
        JSONDecodeError: If the JSON file is not valid.

    """
    with open(fname_settings, "r") as f:
        settings = json.load(f)

    if to_namespace:
        settings = SimpleNamespace(**settings)

    settings.date_min = str(settings.date_start)
    settings.date_max = str(settings.date_end)

    return settings
