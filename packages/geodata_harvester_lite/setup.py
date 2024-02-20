#copied from Nav's aws_utils package

from setuptools import find_packages, setup

VERSION = '0.0.1'

setup(
    name="geodata_harvester_lite",
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'rasterio',
        'rioxarray',
        'xarray',
        'geopandas',
        'shapely',
        'netCDF4',
        'pandas',
        'numpy',
        'matplotlib',
        'fiona>=1.8.21',
        'owslib==0.27.2',
        'requests==2.28.1'
    ],
	keywords=['geodata', 'harvester'],
)