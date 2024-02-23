
from setuptools import find_packages, setup

VERSION = '0.0.1'

setup(
    name="aws_utils",
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'boto3'
    ],
	keywords=['aws', 'utils'],
)
