
from setuptools import find_packages, setup

VERSION = '0.0.1'

setup(
    name="sensand_gis_utils",
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'pystac_client',
        'rasterio',
        'rioxarray',
        'rio-cogeo',
        'xarray',
        'geopandas',
        'pandas',
        'numpy',
        'matplotlib',
        'owslib==0.27.2',
        'requests',
        'pyproj'
    ],
	keywords=['gis', 'utils', 'stac'],
	package_data={'data': ['*.json']}
)
