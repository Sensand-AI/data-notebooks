from setuptools import find_packages, setup

VERSION = '0.0.1'

# by defining requirements here, no requirements.txt file is needed.
setup(
    name="geodata_fetch",
    version=VERSION,
    package_dir={"": "geodata"},
    packages=find_packages(where="geodata"),
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
    ]
)