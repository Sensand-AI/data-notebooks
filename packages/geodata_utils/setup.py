from setuptools import find_packages, setup

VERSION = '0.0.1'

setup(
    name="geodata_utils", #this should be the name of the PARENT sir, not geodata_fetch
    version=VERSION,
    packages=find_packages(),
    install_requires=[
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
    include_package_data=True,
    package_data={
        'geodata_utils': ['config/*.json']
    }
)