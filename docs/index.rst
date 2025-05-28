.. .. GreenTo Documentation documentation master file, created by
..    sphinx-quickstart on Wed Apr  2 10:06:52 2025.
..    You can adapt this file completely to your liking, but it should at least
..    contain the root `toctree` directive.
===================================
GreenTo documentation
===================================

Date: May 6, 2025  Version: 0.1.0

Project and idea by the `University of Turin <https://www.unito.it>`_ under MIT License.

Useful links: `Source Repository <https://github.com/lorenzopelanda/geo-analysis>`_ | `Issues & Ideas <https://github.com/lorenzopelanda/geo-analysis/issues>`_ | `Changelog <changelog.html>`_

**GreenTo** is a Python library designed for analyzing geographic data,
including OpenStreetMap (OSM), Copernicus data and Global Human
Settlement Population (GHS-POP) data. This library provides tools for
downloading, processing, and visualizing geographic data to help with
urban planning, environmental analysis, specifically for green areas.

.. raw:: html

   <div class="container">
     <div class="row">
       <div class="col-lg-6 col-md-6 col-sm-12">
         <div class="card">
           <div class="card-body">
             <h2 class="card-title text-center">
               <i class="fas fa-running"></i> Getting started
             </h2>
             <p class="card-text">
               New to <strong>GreenTo</strong>? Check out the getting started guides.
               They contain an introduction to GreenTo's main
               concepts and links to additional tutorials.
             </p>
             <div class="text-center">
               <a href="README.html" class="btn btn-primary btn-block">To the getting started guides</a>
             </div>
           </div>
         </div>
       </div>
       <div class="col-lg-6 col-md-6 col-sm-12">
         <div class="card">
           <div class="card-body">
             <h2 class="card-title text-center">
               <i class="fas fa-book"></i> Examples
             </h2>
             <p class="card-text">
               This section provides usage examples on the
               key concepts of GreenTo.
             </p>
             <div class="text-center">
               <a href="EXAMPLES.html" class="btn btn-primary btn-block">To the examples</a>
             </div>
           </div>
         </div>
       </div>
     </div>
     <div class="row mt-4">
    <div class="col-lg-6 col-md-6 col-sm-12">
      <div class="card">
        <div class="card-body">
          <h2 class="card-title text-center">
            <i class="fas fa-code"></i> API reference
          </h2>
          <p class="card-text">
            The reference guide contains a detailed description of
            the GreenTo API. The reference describes how the
            methods work and which parameters can be used. It
            assumes that you have an understanding of the key
            concepts.
          </p>
          <div class="text-center">
            <a href="modules.html" class="btn btn-primary btn-block">To the reference guide</a>
          </div>
        </div>
      </div>
    </div>
    <div class="col-lg-6 col-md-6 col-sm-12">
      <div class="card">
        <div class="card-body">
          <h2 class="card-title text-center">
            <i class="fas fa-laptop-code"></i> Jupyter Notebook Examples
          </h2>
          <p class="card-text">
            This section provides Jupyter Notebook examples on the
            key concepts of GreenTo. The examples are with explanations,
            code snippets and graphical outputs to help you understand how to use
            the library effectively.
          </p>
          <div class="text-center">
            <a href="jupyter_examples.html" class="btn btn-primary btn-block">To the notebooks</a>
          </div>
        </div>
      </div>
    </div>
  </div>

.. raw:: html

  <br></br>
  <hr style="border: 3px solid #56996b;">

Example of something done with GreenTo
======================================

Here is an example of what you can do with this library to have the green area per person of a selected zone.

.. code-block:: python

    from greento.boundingbox import bounding_box
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.utils.geo import geo
    from greento.green.copernicus import copernicus as GreenCopernicus
    from greento.metrics.copernicus import copernicus as MetricsCopernicus
    import json

    # Initialize Copernicus downloader
    copernicus_downloader = CopernicusDownloader(
        client_id="your_credential", ...
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

**Output:**

.. code-block:: text

    Green area per person: 198.9388 sqm

.. toctree::
   :maxdepth: 1
   :hidden:

   README
   EXAMPLES
   jupyter_examples
   modules
   


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Additional Information

   GitHub Repository <https://github.com/lorenzopelanda/geo-analysis>