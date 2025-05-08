<link rel="stylesheet" href="{{ '/assets/css/custom.css' | relative_url }}">


# GreenTo

GreenTo is a Python library designed for analyzing geographic data, including OpenStreetMap (OSM), Copernicus data and Global Human Settlement Population (GHS-POP) data. This library provides tools for downloading, processing, and visualizing geographic data to help with urban planning, environmental analysis, specifically for green areas.


## Installation

To install the GreenTo package, follow these steps:

1. Clone the repository:
    ```sh
    git clone https://github.com/lorenzopelanda/geo-analysis.git
    cd geo-analysis
    ```

2. Create a virtual environment (optional but recommended):
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the package and its dependencies:
    ```sh
    pip install .
    ```

  <br></br>
  <hr style="border: 3px solid #56996b;">

#### Example of something done with GreenTo

Here is an example of what you can do with this library to have the green area per person of a selected zone.

```python
from greento.boundingbox import boundingbox
from greento.data.copernicus import copernicus as CopernicusDownloader
from greento.utils.geo import geo
from greento.green.copernicus import copernicus as GreenCopernicus
from greento.metrics.copernicus import copernicus as MetricsCopernicus
import json

# Initialize Copernicus downloader
copernicus_downloader = CopernicusDownloader(
    client_id="your_credential",
    ...
)

# Define the bounding box
bbox = boundingbox()
bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)

# Download Copernicus data
copernicus_area = copernicus_downloader.get_data(bounding_box)

# Calculate green area metrics
copernicus_green = GreenCopernicus(copernicus_area)
green_copernicus = copernicus_green.get_green()

metrics = MetricsCopernicus(green_copernicus)
green_area_per_person = metrics.green_area_per_person()

# Output results
green_area_per_person = json.loads(green_area_per_person)
print(f"Green area per person: {green_area_per_person['green_area_per_person']} sqm")

```
#### Output:
```python
    Green area per person: 198.9388 sqm
```
<br>

## Usage examples

For more etailed usage examples, refer to the examples [here](EXAMPLES.md).

## Jupyter notebook examples

There's a directory `examples/notebooks` containing some Jupyter Notebook's files with some real world examples of the library.

## Releases 

All releases are listed [here](CHANGELOG.md).

## Contributing
Contributions are welcome! Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.


## How to Cite

If you use **GreenTo** in your research, please cite it as follows:

```yaml
@software{greento,
  author = {Department of Computer Science, University of Turin},
  title = {GreenTo: A Python library for spatial accessibility metrics of green areas},
  version = {0.1.0},
  doi = {10.1234/greento.2025},
  url = {https://greento.readthedocs.io},
  year = {2025}
}
```

## License
This project is made by the [University of Turin](https://www.unito.it/) licensed under the MIT License - see the [LICENSE](LICENSE) for details.

