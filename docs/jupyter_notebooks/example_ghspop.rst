Example of how to download a raster area using the data.ghspop class
-------------------------------------------------------------------------

Download Raster GSH-POP Area giving an address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.data.ghspop import ghspop
    from greento.boundingbox import boundingbox
    
    query = "Piazza Castello, Torino"
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query=query, method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    print(bounding_box)
    
    shapefile_path = "/home/lorenzo/Desktop/GeoAnalysis/geo-analysis/tiling_schema/WGS84_tile_schema.shp" #shapefile with the GHS-POP tiles, insert here the correct path
    ghs_pop = ghspop(shapefile=shapefile_path)
    
    ghspop_area = ghs_pop.get_data(bounding_box) # get the population area from the bounding box
    ghspop_data = ghspop_area["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    
    plt.imshow(ghspop_data, cmap='gray_r')
    plt.colorbar(label='Population Density')
    plt.title('GHS-POP area of the bounding box')
    plt.show()


.. parsed-literal::

    BoundingBox(7.550917564864865, 44.935175764864866, 7.821187835135135, 45.20544603513514)

                                                                         


.. image:: /jupyter_notebooks/example_ghspop_files/example_ghspop_2_2.png

