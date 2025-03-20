from setuptools import setup, find_packages

setup(
    name='greento',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'shapely',
        'pyproj',
        'pandas',
        'numpy',
        'matplotlib',
        'osmnx',
        'openeo',
        'rasterio',
        'tqdm',
        'geopandas',
        'networkx',
    ],
    entry_points={
        'console_scripts': [
        ],
    },
)