# Settings reader and handler

import urllib
import json
import os
import datetime
from types import SimpleNamespace
import geopandas as gpd
from IPython.display import display, JSON


def DateEncoder(obj):
    """
    JSON encoder for datetime objects.
    """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.strftime('%Y-%m-%d')


def display_settings(fname_settings, print_option = "json"):
    with open(fname_settings, "r") as f:
        settings = json.load(f)
    # Print settings
    if print_option == "display":
        display(JSON(settings))
    elif print_option == "json":
        print(json.dumps(settings, indent=4, sort_keys=True, default=DateEncoder))
    else:
        print("print_option must be 'display' or 'json'")

def check_bbox(settings):
    if (settings.target_bbox is None) | (settings.target_bbox == ""):
        gdfpoints = gpd.read_file(settings.infile)
        longs = gdfpoints[settings.colname_lng].astype(float)
        lats = gdfpoints[settings.colname_lat].astype(float)
        if settings.target_bbox is None:
            settings.target_bbox = (
                min(longs) - 0.05,
                min(lats) - 0.05,
                max(longs) + 0.05,
                max(lats) + 0.05,
            )
    assert len(settings.target_bbox) == 4, "There must be 4 values in bbox list"
    assert settings.target_bbox[2] > settings.target_bbox[0], "Bounding box[0] must be smaller than box[2]"
    assert settings.target_bbox[3] > settings.target_bbox[1], "Bounding box[1] must be smaller than box[3]"
    return settings


def main(fname_settings, to_namespace=True):
    with open(fname_settings, "r") as f:
        settings = json.load(f)
    # Parse settings dictinary as namespace (settings are available as
    # settings.variable_name rather than settings['variable_name'])
    if to_namespace:
        settings = SimpleNamespace(**settings)

    # Check if bbox is valid
    settings = check_bbox(settings)

    # convert dates to strings if not already
    settings.date_min = str(settings.date_start)
    settings.date_max = str(settings.date_end)

    return settings