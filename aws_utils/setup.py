
from setuptools import find_packages, setup

setup(
    name="aws_utils",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'boto3'
    ],
)
