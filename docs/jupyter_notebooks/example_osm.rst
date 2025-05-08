Example of how to download a vector area using the data.osm class
----------------------------------------------------------------------

Download Vector OSM Area giving a bounding box and convert to raster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.osm import osm as OSMDownloader
    from greento.utils.vector import vector
    from greento.green.osm import osm as GreenOSM
    
    
    
    query = "Piazza Castello, Torino"
    shapefile = "../../tiling_schema/WGS84_tile_schema.shp"
    
    copernicus_downloader = CopernicusDownloader(
        client_id="your_credential",
        client_secret="your_credential",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        use_oidc=True
    )
    osm_downloader = OSMDownloader()
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query=query, method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    print(bounding_box)
    
    # get the raster area of the bounding box
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    # get the vector area of the bounding box
    osm_area = osm_downloader.get_data(bounding_box)
    
    
    green_osm = GreenOSM(osm_area)
    
    green_osm_area = green_osm.get_green() # get the green areas from the OSM data
    utils = vector(green_osm_area)
    green_osm_raster = utils.to_raster(copernicus_area) # convert the green areas to raster, it's passed a raster for the reference of the raster data
    
    raster_osm_data = green_osm_raster["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    
    plt.imshow(raster_osm_data, cmap='gray_r')
    plt.title('OSM raster area of the bounding box with the green areas')
    plt.show()


.. parsed-literal::

    BoundingBox(7.550794238386118, 44.93585061486487, 7.821064508656388, 45.20612088513514)


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:06, 12.06it/s]

.. parsed-literal::

    Authenticated using refresh token.


.. image:: /jupyter_notebooks/example_osm_files/example_osm_2_4.png


Download Vector OSM Area giving a bounding box with the network type and convert to raster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.osm import osm as OSMDownloader
    from greento.traffic.traffic import traffic
    from greento.utils.vector import vector
    from greento.green.osm import osm as GreenOSM
    
    query = "Piazza Castello, Torino"
    
    copernicus_downloader = CopernicusDownloader(
        client_id="your_credential",
        client_secret="your_credential",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        use_oidc=True
    )
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query=query, method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    print(bounding_box)
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    osm_area = OSMDownloader()
    osm_area = osm_area.get_data(bounding_box)
    
    # get the vector area of the bounding box with all the network for the public transport
    traffic = traffic(bounding_box)
    osm_area_traffic = traffic.get_traffic_area("all_public") # get the traffic areas from the OSM data
    
    utils = vector(osm_area_traffic)
    osm_area_traffic_raster = utils.to_raster(copernicus_area) # convert the vector area to a raster area
    osm_area_traffic_data = osm_area_traffic_raster["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    
    plt.imshow(osm_area_traffic_data, cmap='gray_r')
    plt.title('OSM raster area of the bounding box with the newtwork type public transport')
    plt.show()


.. parsed-literal::

    BoundingBox(7.550917564864865, 44.935175764864866, 7.821187835135135, 45.20544603513514)


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:06, 12.35it/s]

.. parsed-literal::

    Authenticated using refresh token.
                                                                                      


.. image:: /jupyter_notebooks/example_osm_files/example_osm_4_4.png

