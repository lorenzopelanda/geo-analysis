<link rel="stylesheet" href="{{ '/assets/css/custom.css' | relative_url }}">

# GreenTo Examples

- [Defining a Bounding Box](#defining-a-bounding-box)
    - [From Coordinates](#from-coordinates)
    - [From Center Radius](#from-center-radius)
    - [From GeoJSON](#from-geojson)
- [Downloading OSM Data](#downloading-osm-data)   
- [Downloading Copernicus Data](#downloading-copernicus-data)
- [Downloading GHS-POP Data](#downloading-ghs-pop-data) 
- [Obtaining green areas for OSM](#obtaining-green-areas-for-osm)
- [Obtaining green areas for Copernicus](#obtaining-green-areas-for-copernicus)
- [Obtaining the traffic network](#obtaining-the-traffic-network)
- [Green metrics](#green-metrics)
    - [Get the OSM green metrics](#get-the-osm-green-metrics)
    - [Get the Copernicus green metrics](#get-the-copernicus-green-metrics)
- [Green distances](#green-distances)
    - [Distance to nearest green area for OSM data](#distance-to-nearest-green-area-for-osm-data)
    - [Distance to nearest green area for Copernicus data](#distance-to-nearest-green-area-for-copernicus-data)
- [Utils functions](#utils-functions)
    - [`raster` functions](#raster-functions)
    - [`vector` functions](#vector-functions)
    - [General functions](#general-functions)
<br><br>

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



<br><br>

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



<br><br>


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



<br><br>



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



<br><br>



---
## Obtaining green areas for OSM

This example demonstrates how to filter the downloaded data from OpenStreetMap to get only the green areas for a bounding box using `GreenOSM` class.
It's supposed you already have downloaded the data from the `OSMDownloader` class.
We use the function `get_green()`, you can pass some green areas of your choise in a dictionary way using the tags from OpenStreetMap unless it uses some default type of green areas. 

```python
from greento.green.GreenOSM import GreenOSM

green = GreenOSM(osm_area) #the one downloaded from OSMDownloader
green_area = green.get_green()

```



<br><br>



---
## Obtaining green areas for Copernicus

This example demonstrates how to filter the downloaded data from Copernicus to get only the green areas for a bounding box using `GreenCopernicus` class.
It's supposed you already have downloaded the data from the `CopernicusDownloader` class.
We use the function `get_green()`, you can pass some green areas of your choise in a set in the number format of the specified satellites system unless it uses some default type of green areas. 

```python
from greento.green.GreenCopernicus import GreenCopernicus

green = GreenCopernicus(copernicus_area) #the one downloaded from CopernicusDownloader
green_area = green.get_green()

```



<br><br>



---
## Obtaining the traffic network

This example demonstrates how to get the traffic network map of the bounding box selected using the `Traffic` class.


### Create a bounding box using the `BoundingBox` class:

```python
from greento.boundingbox.BoundingBox import BoundingBox

bbox = BoundingBox()
bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
print(bounding_box)
```

### Get the traffic network with `Traffic` class

You have to pass a vehicle used to move like: `walk, bike, drive, all_public, all_private, all`.

```python
from greento.traffic.Traffic import Traffic

traffic = Traffic(bounding_box)
traffic_area = traffic.get_traffic_area("walk")

```



<br><br>

---

# Green metrics
<br>

## Get the OSM green metrics

### `green_area_per_person()`

This function calculates the square meters of green areas in the bounding box per person using the data from OpenStreetMap with only the green areas and in raster form and the data from GHS-POP. The green data must be in raster form, so you have to rasterize them using `to_raster(reference_raster)` function in `utils.vector.VectorUtils`.

```python
from greento.metrics.MetricsOSM import MetricsOSM

metrics_osm = MetricsOSM(osm_green, traffic_network, ghspop)
green_are_per_person = metrics_osm.green_area_per_person()

```
<br>

### `green_isochrone_green(lat, lon, max_time, network_type)`

This function calculates from a starting point the max reachable green areas with a time limit and a network type. Using the data from OpenStreetMap with only the green areas and in raster form and the data from GHS-POP. The green data must be in raster form, so you have to rasterize them using `to_raster(reference_raster)` function in `utils.vector.VectorUtils`.

```python
from greento.metrics.MetricsOSM import MetricsOSM

metrics_osm = MetricsOSM(osm_green, traffic_network, ghspop)
max_reachable_green = metrics_osm.green_isochrone_green(45.0628, 7.6781, 12, "walk")

```



<br><br>


## Get the Copernicus green metrics

### `green_area_per_person()`

This function calculates the square meters of green areas in the bounding box per person using the data from Copernicus with only the green areas and the data from GHS-POP.

```python
from greento.metrics.MetricsCopernicus import MetricsCopernicus

metrics_copernicus = MetricsCopernicus(copernicus_green, traffic_network, ghspop)
green_are_per_person = metrics_copernicus.green_area_per_person()

```
<br>

### `green_isochrone_green(lat, lon, max_time, network_type)`

This function calculates from a starting point the max reachable green areas with a time limit and a network type. Using the data from Copernicus with only the green areas and the data from GHS-POP.

```python
from greento.metrics.MetricsCopernicus import MetricsCopernicus

metrics_copernicus = MetricsCopernicus(copernicus_green, traffic_network, ghspop)
max_reachable_green = metrics_copernicus.green_isochrone_green(45.0628, 7.6781, 12, "walk")

```



<br><br>

---

# Green distances
<br>

## Distance to nearest green area for OSM data

### `get_nearest_green_position(lat, lon)`

This function calculate the coordinates of the nearest green area for the OSM data and the traffic area downloaded before.
The green data must be in raster form, so you have to rasterize them using `to_raster(reference_raster)` function in `utils.vector.VectorUtils`.
The functions returns a tuple with the nearest green latitude and longitude.

```python
from greento.distance.DistanceOSM import DistanceOSM

distance_osm = DistanceOSM(green_osm_raster, traffic_area)
green_lat, green_lon = distance_osm.get_nearest_green_position(lat, lon)

```
<br>

### `directions(lat1, lon1, lat2, lon2, transport_mode)`

This function calculates the necessary time to reach a target point from a starting one. 
This function returns a json response containing the distance in km and the ncessarity time to reach the target in the selected transport mode.

```python
from greento.distance.DistanceOSM import DistanceOSM

distance_osm = DistanceOSM(green_osm_raster, traffic_area)
green_lat, green_lon = distance_osm.get_nearest_green_position(lat, lon)
distance = distance_osm.directions(lat, lon, green_lat, green_lon, "walk")
print(f"Distance \n {distance} ")

```



<br><br>


## Distance to nearest green area for Copernicus data

### `get_nearest_green_position(lat, lon)`

This function calculate the coordinates of the nearest green area for the Copernicus data and the traffic area downloaded before.
The functions returns a tuple with the nearest green latitude and longitude.

```python
from greento.distance.DistanceCopernicus import DistanceCopernicus

distance_copernicus = DistanceCopernicus(green_copernicus, traffic_area)
green_lat, green_lon = distance_copernicus.get_nearest_green_position(lat, lon)

```
<br>

### `directions(lat1, lon1, lat2, lon2, transport_mode)`

This function calculates the necessary time to reach a target point from a starting one. 
This function returns a json response containing the distance in km and the ncessarity time to reach the target in the selected transport mode.

```python
from greento.distance.DistanceCopernicus import DistanceCopernicus

distance_copernicus = DistanceCopernicus(green_copernicus, traffic_area)
green_lat, green_lon = distance_copernicus.get_nearest_green_position(lat, lon)
distance = distance_copernicus.directions(lat, lon, green_lat, green_lon, "walk")
print(f"Distance \n {distance} ")

```

<br><br>



---
## Utils functions

This example shows how some functions in the `utils` package work.

<br>

### `raster` functions

#### Get the land usage percentages for the Copernicus data using `get_land_use_percentages()`

It is supposed that the Copernicus data are already downloaded for the interested area.
The function returns a json object with all the informations.

```python
from greento.utils.raster.RasterUtils import RasterUtils

utils = RasterUtils(copernicus_area)
land_use_percentages = utils.get_land_use_percentages()
```

#### Transform the CRS of raster data with `raster_to_crs()`

The raster data have to be already downloaded.

```python
from greento.utils.raster.RasterUtils import RasterUtils

utils = RasterUtils(copernicus_area)
raster_new = utils.raster_to_crs("EPSG:3857")
```

#### Filter the Copernicus green data with the OSM green ones using `filter_with_osm()`

It is supposed that the Copernicus green data and the OpenStreetMap green data are already filtered.
The OSM data should be in raster format.
This function combinates the two datasets to have a more appropriate green cover

```python
from greento.utils.raster.RasterUtils import RasterUtils

utils = RasterUtils(copernicus_area)
copernicus_filtered = utils.filter_with_osm(copernicus_green, osm_green)
```
<br>

### `vector` functions

#### Get the land usage percentages for the OSM data using `get_land_use_percentages()`

It is supposed that the OpenStreetMap data are already downloaded for the interested area.
The function returns a json object with all the informations.

```python
from greento.utils.vector.VectorUtils import VectorUtils

utils = VectorUtils(osm_area)
land_use_percentages = utils.get_land_use_percentages()
```

#### Convert the vector data in raster format using `to_raster()`

It is supposed that the OpenStreetMap data are already downloaded for the interested area.
The function need to have also sme raster data as a reference.
In this example are used the data from Copernicus

```python
from greento.utils.vector.VectorUtils import VectorUtils

utils = VectorUtils(osm_area)
raster_data = utils.to_raster(copernicus_area)
```
<br>

### General functions

#### `_calculate_travel_time(distance_meters, transport_mode)`

This function calculate the estimated time for a specific vehicle and a specified distance in meters.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils._calculate_travel_time(600, "walk")
```

#### `get_coordinates_from_address(address)`

This function converts the given address in coordinates returning a tuple with latitude and longitude.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils.get_coordinates_from_address("Via Garibaldi 5, Torino")
```

#### `get_address_from_coordinates(latitude, longitude)`

This function converts the given coordinates returning an address corresponding.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils.get_address_from_coordinates(45.0705, 7.6936)
```

#### `get_coordinates_max_population(ghs_pop)`

This function gives the coordinates corresponding to the point where there's the max number of people living.
It returns a tuple with latitude, longitude.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils.get_coordinates_max_population(ghs_pop)
```

#### `haversine_distance(lon1, lat1, lons2, lats2)`

This function calculate the euclidean distance from two points giving the latitude and longitude of each.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils.haversine_distance(lon1, lat1, 7.6784, 45.0637)
```

#### `adjust_detail_level(osm, copernicus, ghs_pop)`

This function need three raster datasets.
It returns the two of them with the lowest resolution upscaled.

```python
from greento.utils.GeoUtils import GeoUtils

utils = GeoUtils()
utils.adjust_detail_level(osm, copernicus, ghs_pop)
```
<br>
#### BACK to [Homepage](README.md)




