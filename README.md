# GreenTo

GreenTo is a Python library designed for analyzing geographic data, including OpenStreetMap (OSM), Copernicus data and Global Human Settlement Population (GHS-POP) data. This library provides tools for downloading, processing, and visualizing geographic data to help with urban planning, environmental analysis, specifically for green areas.

## Code repository

[Here](https://github.com/lorenzopelanda/geo-analysis) there's the code repository.


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

## Usage examples

For detailed usage examples, refer to the examples [here](EXAMPLES.md).

<script>
  // Esegui questo codice quando la pagina è completamente caricata
  window.onload = function() {
    // Trova l'elemento header
    var header = document.querySelector('.page-header');
    if (header) {
      // Applica l'immagine di sfondo
      header.style.backgroundImage = "url('https://raw.githubusercontent.com/lorenzopelanda/geo-analysis/main/assets/images/background.jpg')";
      header.style.backgroundSize = "cover";
      header.style.backgroundPosition = "center";
    }
  };
</script>

