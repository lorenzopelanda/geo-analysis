# GreenTo Examples

- [Defining a Bounding Box](#defining-a-bounding-box)
    - [From Coordinates](#from-coordinates)
    - [From Center Radius](#from-center-radius)
    - [From GeoJSON](#from-geojson)
- [Downloading OSM Data](#downloading-osm-data)   
- [Downloading Copernicus Data](#downloading-copernicus-data)
- [Downloading GHS-POP Data](#downloading-ghs-pop-data) 
---



## Defining a Bounding Box

### From Coordinates

This example demonstrates how to create a bounding box from specific coordinates.

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(
    query=None,
    method="from_coordinates",
    min_x=7.661, min_y=45.064, max_x=7.700, max_y=45.090
)
print(bounding_box)
```

### From Center Radius

This example demonstrates how to create a bounding box from a center point and radius.

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(
    query="Piazza Castello, Torino",
    method="from_center_radius",
    radius_km=15
)
print(bounding_box)
```

### From GeoJSON

This example demonstrates how to create a bounding box from a GeoJSON object.

```python
from greento.boundingbox.BoundingBox import BoundingBox

geojson = {
    "type": "Polygon",
    "coordinates": [
        [
            [7.661, 45.064],
            [7.700, 45.064],
            [7.700, 45.090],
            [7.661, 45.090],
            [7.661, 45.064]
        ]
    ]
}

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(
    query=None,
    method="from_geojson",
    geojson=geojson
)
print(bounding_box)
```


---



## Downloading OSM Data

This example demonstrates how to download OpenStreetMap data for a specific bounding box

### Create a bounding box using the `BoundingBox` class:

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
print(bounding_box)
```

### Download OSM data using the `OSMDownloader` class:

```python
from greento.data.osm.OSMDownloader import OSMDownloader

osm_downloader = OSMDownloader()
osm_area = osm_downloader.get_data(bounding_box)
```


---




## Downloading Copernicus Data

This example demonstrates how to download Copernicus raster data for a specific bounding box

### Create a bounding box using the `BoundingBox` class:

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
print(bounding_box)
```

### Download Copernicus data using the `CopernicusDownloader` class:

You can choose between using the refresh token like in the example, or `use_oidc=True` to use the authentication in the browser. 

```python
from greento.data.copernicus.CopernicusDownloader import CopernicusDownloader

copernicus_downloader = CopernicusDownloader(
        client_id="CLIENT-ID",
        client_secret="CLIENT-SECRET",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        use_oidc=False
)

copernicus_area = copernicus_downloader.get_data(bounding_box)
```


---





## Downloading GHS-POP Data

This example demonstrates how to download Global Human Settlement Population (GHS-POP) raster data for a specific bounding box

### Create a bounding box using the `BoundingBox` class:

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
print(bounding_box)
```
### Download GHS-POP data using the `GHSPOPDownloader` class:

You have to pass an attribute containing the path for the shapefile, in the folder `tiling_schema` there's a `.shp`, this file path should be passed to the class.

```python
from greento.data.ghspop.GHSPOPDownloader import GHSPOPDownloader

shapefile_path = "/your-path/tiling_schema/WGS84_tile_schema.shp"
ghspop_data = GHSPOPDownloader(shapefile_path)

ghspop = ghspop_downloader.get_data(bounding_box)
```


---






