from setuptools import setup, find_packages

setup(
    name='geo-analysis',
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
        'geopandas'
    ],
    entry_points={
        'console_scripts': [
            # Aggiungi eventuali script eseguibili qui
        ],
    },
)