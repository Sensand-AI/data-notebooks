import json
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
from gis_utils.dataframe import get_bbox_from_geodf

from geodata_fetch.harvest import DataSourceFactory, Settings


class create_test_data(unittest.TestCase):
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, create=True)
    def dem_test_data(self, mock_open, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        mock_makedirs.return_value = None

        output_dir = "/fake/path"
        mock_makedirs.assert_called_once_with(output_dir)
        mock_open.assert_called_once_with(output_dir + "/dem.json", "w")
        geojson = {
            "body": {
                "type": "FeatureCollection",
                "name": "dissolved-boundaries",
                "crs": {
                    "type": "name",
                    "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
                },
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"fid": 1},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [116.26012130269045, -29.225295369642396],
                                    [116.261724812149055, -29.241374854584375],
                                    [116.283751968396274, -29.256813692452539],
                                    [116.284342735038919, -29.268250184258388],
                                    [116.292247755352392, -29.265992437426529],
                                    [116.292360282331941, -29.293057573630019],
                                    [116.314865678242256, -29.293523728033122],
                                    [116.326259034921833, -29.293033039128805],
                                    [116.326315298411629, -29.305397680579894],
                                    [116.355065941687045, -29.307016748931797],
                                    [116.355065941687045, -29.306575187382712],
                                    [116.383366477044206, -29.307384715430175],
                                    [116.384322956370426, -29.290407813444993],
                                    [116.387586238777402, -29.282629879611861],
                                    [116.386517232471661, -29.259807919053017],
                                    [116.359201308185533, -29.259488866292969],
                                    [116.359229439930417, -29.259243440415627],
                                    [116.35242155766754, -29.259292525638209],
                                    [116.352140240218716, -29.220237788279107],
                                    [116.302234524787593, -29.223503148505326],
                                    [116.281388901825679, -29.2239696200396],
                                    [116.26012130269045, -29.225295369642396],
                                ]
                            ],
                        },
                    }
                ],
            }
        }
        geojson_data = geojson["body"]
        gdf = gpd.read_file(StringIO(json.dumps(geojson_data)))
        geom = gdf.geometry
        bbox = get_bbox_from_geodf(geojson_data)
        gdf_lon = gdf.to_crs(3857).centroid.x[0]
        gdf_lat = gdf.to_crs(3857).centroid.y[0]

        json_data = {
            "property_name": "buckley_farm",
            "outpath": "/fake/path",
            "data_mask": "true",
            "target_res": "1",
            "target_crs": "EPSG:4326",
            "date_start": "2022-10-01",
            "date_end": "2022-11-30",
            "target_centroid_lat": gdf_lat,
            "target_centroid_lng": gdf_lon,
            "time_intervals": "0",
            "target_sources": {"DEM": "DEM"},
            "target_bbox": bbox,
            "add_buffer": "false",
            "resample": "false",
        }

        data = json.dumps(json_data)
        json_file_like = StringIO(data)

        return json_file_like, geom


class TestDEMDataSource(unittest.TestCase):
    @patch("your_package.harvest.dem_harvest")
    def test_fetch_data(self, mock_dem_harvest):
        # Setup
        mock_instance = mock_dem_harvest.return_value
        mock_instance.get_dem_layers.return_value = [
            "path/to/dem1.tif",
            "path/to/dem2.tif",
        ]
        settings = Settings(
            SimpleNamespace(
                target_sources={"DEM": ["layer1", "layer2"]},
                property_name="elevation",
                target_bbox=(0, 0, 10, 10),
                outpath="/fake/path",
            )
        )

        dem_source = DataSourceFactory.get_data_source("DEM")

        # Action
        result = dem_source.fetch_data(settings)

        # Assert
        self.assertEqual(result, ["path/to/dem1.tif", "path/to/dem2.tif"])
        mock_instance.get_dem_layers.assert_called_once_with(
            property_name="elevation",
            layernames=["layer1", "layer2"],
            bbox=(0, 0, 10, 10),
            outpath="/fake/path",
        )
