Example of how to find the nearest green area using the green.copernicus and metrics.copernicus, green.osm and metrics.osm class
----------------------------------------------------------------------------------------------------------------------------------

Copernicus
----------

Find the green area metrics for Copernicus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.ghspop import ghspop as GHSPOPDownloader
    from greento.green.copernicus import copernicus as GreenCopernicus
    from greento.utils.geo import geo
    from greento.metrics.copernicus import copernicus as MetricsCopernicus
    from greento.traffic.traffic import traffic
    import json
    
    copernicus_downloader = CopernicusDownloader(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    shapefile_path = "/home/lorenzo/Desktop/GeoAnalysis/geo-analysis/tiling_schema/WGS84_tile_schema.shp"
    ghspop = GHSPOPDownloader(shapefile=shapefile_path)
    ghspop_area = ghspop.get_data(bounding_box)
    
    traffic = traffic(bounding_box)
    traffic_area = traffic.get_traffic_area("walk")
    
    address = "Via Principessa Clotilde 28/B, Torino"
    lat, lon = geo().get_coordinates_from_address(address)
    print(f"Coordinates for the starting point: {lat}, {lon}")
    
    copernicus_green = GreenCopernicus(copernicus_area)
    green_copernicus = copernicus_green.get_green() # get the green area from the Copernicus data
    
    metrics = MetricsCopernicus(green_copernicus, traffic_area, ghspop_area) # it's passed the green area, the traffic network and the population area
    network_type = "walk"
    green_area_per_person = metrics.green_area_per_person() # returns a json object with the green area per person
    isochrone_green = metrics.get_isochrone_green(lat, lon, 12, network_type) # returns a json object with the green area percentage, the max time to reach the green area and the green area in sqm walked
    
    green_area_per_person = json.loads(green_area_per_person)
    isochrone_green = json.loads(isochrone_green)
    print("-------- COPERNICUS DATA --------")
    green_area_per_person = green_area_per_person["green_area_per_person"]
    print(f"Green area per person: {green_area_per_person} sqm")
    green_area_percentage = isochrone_green["green_area_percentage"]
    time = isochrone_green["max_time"]
    areasq = isochrone_green["green_area_sqm"]
    print(f"Time max to reach the green area for the network_type {network_type}: {time} minutes")
    print(f"Green area percentage: {green_area_percentage}%")
    print(f"Green area in sqm walked: {areasq} sqm")



.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:03<00:12,  6.57it/s]

.. parsed-literal::

    Authenticated using refresh token.


                                                                                          

.. parsed-literal::

    Coordinates for the starting point: 45.0813291, 7.6675035


                                                                                                               

.. parsed-literal::

    -------- COPERNICUS DATA --------
    Green area per person: 353.845 sqm
    Time max to reach the green area for the network_type walk: 12 minutes
    Green area percentage: 16.32%
    Green area in sqm walked: 11800 sqm


    

Find the nearest green position and return the distances for Copernicus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.ghspop import ghspop
    from greento.green.copernicus import copernicus as GreenCopernicus
    from greento.utils.geo import geo
    from greento.distance.copernicus import copernicus as DistanceCopernicus
    from greento.traffic.traffic import traffic
    import json
    
    copernicus_downloader = CopernicusDownloader(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    shapefile_path = "/home/lorenzo/Desktop/GeoAnalysis/geo-analysis/tiling_schema/WGS84_tile_schema.shp"
    ghspop_data = ghspop(shapefile=shapefile_path)
    ghspop_area = ghspop_data.get_data(bounding_box)
    
    traffic = traffic(bounding_box)
    traffic_area = traffic.get_traffic_area("walk")
    
    address = "Via Principessa Clotilde 28/B, Torino"
    lat, lon = geo().get_coordinates_from_address(address)
    
    
    copernicus_green = GreenCopernicus(copernicus_area)
    green_copernicus = copernicus_green.get_green() # get the green area from the Copernicus data
    
    distance_copernicus = DistanceCopernicus(green_copernicus, traffic_area)
    green_lat, green_lon = distance_copernicus.get_nearest_green_position(lat, lon)
    print("-------- COPERNICUS DATA --------")
    print(f"Coordinates for the starting point: {lat}, {lon}")
    print(f"Nearest green position: {green_lat}, {green_lon}")
    distance = distance_copernicus.directions(lat, lon, green_lat, green_lon, "walk")
    print(f"Distance \n {distance} ")



.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:07, 10.12it/s]

.. parsed-literal::

    Authenticated using refresh token.


                                                                                          

.. parsed-literal::

    -------- COPERNICUS DATA --------
    Coordinates for the starting point: 45.0813291, 7.6675035
    Nearest green position: 45.08191255180181, 7.667669238386118


                                                                                

.. parsed-literal::

    Distance 
     {"distance_km": 0.0629, "estimated_time_minutes": 0.9} 



    

OSM
---

Find the green area details for OSM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.ghspop import ghspop as GHSPOPDownloader
    from greento.data.osm import osm as OSMDownloader
    from greento.green.copernicus import copernicus as GreenCopernicus
    from greento.utils.geo import geo
    from greento.green.osm import osm as GreenOSM
    from greento.metrics.osm import osm as MetricsOSM
    from greento.utils.raster import raster
    from greento.distance.copernicus import copernicus as DistanceCopernicus
    from greento.distance.osm import osm as DistanceOSM
    from greento.utils.vector import vector
    from greento.traffic.traffic import traffic
    import json
    
    copernicus_downloader = CopernicusDownloader(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    
    osm_downloader = OSMDownloader()
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    osm_area = osm_downloader.get_data(bounding_box)
    
    shapefile_path = "/home/lorenzo/Desktop/GeoAnalysis/geo-analysis/tiling_schema/WGS84_tile_schema.shp"
    ghspop = GHSPOPDownloader(shapefile=shapefile_path)
    ghspop_area = ghspop.get_data(bounding_box)
    
    traffic = traffic(bounding_box)
    traffic_area = traffic.get_traffic_area("walk")
    
    address = "Via Principessa Clotilde 28/B, Torino"
    lat, lon = geo().get_coordinates_from_address(address)
    print(f"Coordinates for the starting point: {lat}, {lon}")
    
    osm_green = GreenOSM(osm_area)
    green_osm = osm_green.get_green() # get the green area from the OSM data
    
    green_osm_raster = vector(green_osm).to_raster(copernicus_area)
    
    metrics = MetricsOSM(green_osm_raster, traffic_area, ghspop_area) # it's passed the green area, the traffic network and the population area
    network_type = "walk"
    green_area_per_person = metrics.green_area_per_person() # returns a json object with the green area per person
    isochrone_green = metrics.get_isochrone_green(lat, lon, 12, network_type) # returns a json object with the green area percentage, the max time to reach the green area and the green area in sqm walked
    
    green_area_per_person = json.loads(green_area_per_person)
    isochrone_green = json.loads(isochrone_green)
    print("-------- OSM DATA --------")
    green_area_per_person = green_area_per_person["green_area_per_person"]
    print(f"Green area per person: {green_area_per_person} sqm")
    green_area_percentage = isochrone_green["green_area_percentage"]
    time = isochrone_green["max_time"]
    areasq = isochrone_green["green_area_sqm"]
    print(f"Time max to reach the green area for the network_type {network_type}: {time} minutes")
    print(f"Green area percentage: {green_area_percentage}%")
    print(f"Green area in sqm walked: {areasq} sqm")



.. parsed-literal::

    Downloading Copernicus data:  60%|██████    | 60/100 [00:01<00:01, 37.97it/s]

.. parsed-literal::

    Authenticated using refresh token.


                                                                                          

.. parsed-literal::

    Coordinates for the starting point: 45.0813291, 7.6675035


                                                                                                        

.. parsed-literal::

    -------- OSM DATA --------
    Green area per person: 198.9388 sqm
    Time max to reach the green area for the network_type walk: 12 minutes
    Green area percentage: 10.66%
    Green area in sqm walked: 7700 sqm


    

.. code-block:: python

    from greento.boundingbox import boundingbox
    from greento.data.copernicus import copernicus as CopernicusDownloader
    from greento.data.ghspop import ghspop as GHSPOPDownloader
    from greento.data.osm import osm as OSMDownloader
    from greento.utils.geo import geo
    from greento.green.osm import osm as GreenOSM
    from greento.distance.copernicus import copernicus as DistanceCopernicus
    from greento.utils.vector import vector
    from greento.traffic.traffic import traffic
    import json
    
    copernicus_downloader = CopernicusDownloader(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    
    bbox = boundingbox()
    osm_downloader = OSMDownloader()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    osm_area = osm_downloader.get_data(bounding_box)
    shapefile_path = "/home/lorenzo/Desktop/GeoAnalysis/geo-analysis/tiling_schema/WGS84_tile_schema.shp"
    ghspop = GHSPOPDownloader(shapefile=shapefile_path)
    ghspop_area = ghspop.get_data(bounding_box)
    
    traffic = traffic(bounding_box)
    traffic_area = traffic.get_traffic_area("walk")
    
    address = "Via Principessa Clotilde 28/B, Torino"
    lat, lon = geo().get_coordinates_from_address(address)
    
    
    osm_green = GreenOSM(osm_area)
    green_osm = osm_green.get_green() # get the green area from the OSM data
    
    green_osm_raster = vector(green_osm).to_raster(copernicus_area) # convert the green area to raster
    
    distance_osm = DistanceOSM(green_osm_raster, traffic_area)
    green_lat, green_lon = distance_osm.get_nearest_green_position(lat, lon)
    print("-------- OSM DATA --------")
    print(f"Coordinates for the starting point: {lat}, {lon}")
    print(f"Nearest green position: {green_lat}, {green_lon}")
    distance = distance_osm.directions(lat, lon, green_lat, green_lon, "walk")
    print(f"Distance \n {distance} ")


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:07, 11.04it/s]

.. parsed-literal::

    Authenticated using refresh token.



                                                                                          

.. parsed-literal::

    -------- OSM DATA --------
    Coordinates for the starting point: 45.0813291, 7.6675035
    Nearest green position: 45.08146130175053, 7.6677779626949185


                                                                                

.. parsed-literal::

    Distance 
     {"distance_km": 0.0, "estimated_time_minutes": 0.0} 

    
