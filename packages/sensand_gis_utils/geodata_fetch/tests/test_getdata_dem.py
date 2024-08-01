# import json
# from io import StringIO
# from unittest.mock import patch

# import geopandas as gpd
# import pytest
# from gis_utils.dataframe import get_bbox_from_geodf


# # use pytest.fixture to setup permanent, reusable ode called before each test. in this case, the mock data.
# @pytest.fixture
# def create_dem_config_data():
#     """
#     This is test data for the dem configuration json file found in the 'data' directory. This is NOT the data that the end user provides to make the data harvest, this is what is 'hardcoded' inside the package itself.
#     """
#     json_data = {
#         "title": "DEM",
#         "description": "Digital Elevation Model (DEM) of Australia derived from STRM with 1 Second Grid - Hydrologically Enforced.",
#         "source_url": "https://www.clw.csiro.au/aclep/soilandlandscapegrid/ProductDetails.html",
#         "license": "CC BY 4.0",
#         "copyright": "© Copyright 2017-2022, Geoscience Australia",
#         "attribution": "Commonwealth of Australia (Geoscience Australia) ",
#         "crs": "EPSG:4326",
#         "bbox": [
#             112.9995833334,
#             -44.0004166670144,
#             153.999583334061,
#             -10.0004166664663,
#         ],
#         "resolution_arcsec": 1,
#         "layers_url": {
#             "DEM": "https://services.ga.gov.au/site_9/services/DEM_SRTM_1Second_Hydro_Enforced/MapServer/WCSServer?request=GetCapabilities&service=WCS"
#         },
#     }

#     data = json.dumps(json_data)
#     json_file_like = StringIO(data)

#     return json_file_like


# @pytest.fixture
# def create_dem_request_data():
#     """
#     This mocks a request for DEM data. This is the data that the end user provides to make the data harvest.
#     """
#     with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
#         mock_exists.return_value = False
#         mock_makedirs.return_value = None

#         output_dir = "/fake/path"
#         mock_makedirs.assert_called_once_with(output_dir)

#         geojson = {
#             "body": {
#                 "type": "FeatureCollection",
#                 "name": "dissolved-boundaries",
#                 "crs": {
#                     "type": "name",
#                     "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
#                 },
#                 "features": [
#                     {
#                         "type": "Feature",
#                         "properties": {"fid": 1},
#                         "geometry": {
#                             "type": "Polygon",
#                             "coordinates": [
#                                 [
#                                     [116.257742946061839, -29.308539062959664],
#                                     [116.257742946061839, -29.215970495733881],
#                                     [116.39048277831013, -29.215970495733881],
#                                     [116.39048277831013, -29.308539062959664],
#                                     [116.257742946061839, -29.308539062959664],
#                                 ]
#                             ],
#                         },
#                     }
#                 ],
#             }
#         }
#         geojson_data = geojson["body"]
#         gdf = gpd.read_file(StringIO(json.dumps(geojson_data)))
#         geom = gdf.geometry
#         bbox = get_bbox_from_geodf(geojson_data)
#         gdf_lon = gdf.to_crs(3857).centroid.x[0]
#         gdf_lat = gdf.to_crs(3857).centroid.y[0]

#         json_data = {
#             "property_name": "buckley_farm",
#             "outpath": "/fake/path",
#             "data_mask": "true",
#             "target_res": "1",
#             "target_crs": "EPSG:4326",
#             "date_start": "2022-10-01",
#             "date_end": "2022-11-30",
#             "target_centroid_lat": gdf_lat,
#             "target_centroid_lng": gdf_lon,
#             "time_intervals": "0",
#             "target_sources": {"DEM": "DEM"},
#             "target_bbox": bbox,
#             "add_buffer": "false",
#             "resample": "false",
#         }

#         data = json.dumps(json_data)
#         json_file_like = StringIO(data)

#     return json_file_like, geom
