Example of how to download a raster area using the data.copernicus class
-----------------------------------------------------------------------------

Download Raster Area giving an address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.data.copernicus import copernicus
    from greento.boundingbox import boundingbox
    
    copernicus_downloader = copernicus(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    # use_oidc=True indicates we are using the client_id and client_secret for authentication
    # with use_oidc=False, we would use the OpenID Connect authentication method
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    # we are using the "from_center_radius" method to get the bounding box coordinates, it gets the bounding box from a center point and a radius in km
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    print(bounding_box)
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    raster_data = copernicus_area["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    cmap_colors = ["white", "lightgreen", "green", "darkgreen", "black"]
    cmap = ListedColormap(cmap_colors[1:])
    plt.imshow(raster_data, cmap=cmap)
    plt.colorbar(label='Land Use Type')
    plt.title('Copernicus World Land Cover Data of the area')
    
    plt.show()


.. parsed-literal::

    boundingbox(7.5504102648648646, 44.93514056486487, 7.820680535135135, 45.20541083513514)


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:06, 11.81it/s]

.. parsed-literal::

    Authenticated using refresh token.


.. image:: /jupyter_notebooks/example_copernicus_files/example_copernicus_2_4.png


Download Raster Area giving the bounding box Geojson data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import json
    from greento.data.copernicus import copernicus
    from greento.boundingbox import boundingbox
    
    
    
    copernicus_downloader = copernicus(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    # use_oidc=True indicates we are using the client_id and client_secret for authentication
    # with use_oidc=False, we would use the OpenID Connect authentication method
    
    # Define the bounding box coordinates with bbox property
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [12.4, 41.8],
                            [12.6, 41.8],
                            [12.6, 42.0],
                            [12.4, 42.0],
                            [12.4, 41.8]
                        ]
                    ]
                },
                "properties": {}
            }
        ]
    }
    
    # Save the GeoJSON data to a file
    with open('bounding_box.geojson', 'w') as f:
        json.dump(geojson_data, f, indent=4)
    
    # Load the GeoJSON data from the file
    with open('bounding_box.geojson', 'r') as f:
        geojson_content = json.load(f)
    
    # Create a BoundingBox instance and use the from_geojson method
    bbox = boundingboxS()
    bounding_box = bbox.get_bounding_box(query=None, method='from_geojson', geojson=geojson_content)
    
    print(bounding_box)
    # we are using the "from_geojson" method to get the bounding box coordinates, it gets the bounding box from a GeoJSON data
    # different methods are available to get the bounding box coordinates, such as "from_coordinates" and "from_geojson"
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    raster_data = copernicus_area["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    cmap_colors = ["white", "lightgreen", "green", "darkgreen", "black"]
    cmap = ListedColormap(cmap_colors[1:])
    plt.imshow(raster_data, cmap=cmap)
    plt.colorbar(label='Land Use Type')
    plt.title('Copernicus World Land Cover Data of the area')
    
    plt.show()


.. parsed-literal::

    BoundingBox(12.4, 41.8, 12.6, 42.0)


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:02<00:08,  9.93it/s]

.. parsed-literal::

    Authenticated using refresh token.


.. image:: /jupyter_notebooks/example_copernicus_files/example_copernicus_4_4.png


Download Raster Area giving the bounding box coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from greento.data.copernicus import copernicus
    from greento.boundingbox import boundingbox
    
    
    copernicus_downloader = copernicus(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
        )
    # use_oidc=True indicates we are using the client_id and client_secret for authentication
    # with use_oidc=False, we would use the OpenID Connect authentication method
    
    # Create a BoundingBox instance and use the from_coordinates method
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query=None, method='from_coordinates', min_x=12.4, min_y=41.8, max_x=12.6, max_y=42.0)
    # we are using the "from_coordinates" method to get the bounding box coordinates, it gets the bounding box from the minimum and maximum coordinates
    
    print(bounding_box)
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    
    raster_data = copernicus_area["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    cmap_colors = ["white", "lightgreen", "green", "darkgreen", "black"]
    cmap = ListedColormap(cmap_colors[1:])
    plt.imshow(raster_data, cmap=cmap)
    plt.colorbar(label='Land Use Type')
    plt.title('Copernicus World Land Cover Data of the area')
    
    plt.show()


.. parsed-literal::

    BoundingBox(12.4, 41.8, 12.6, 42.0)


.. parsed-literal::

    Downloading Copernicus data:  60%|██████    | 60/100 [00:01<00:00, 40.14it/s]

.. parsed-literal::

    Authenticated using refresh token.
                                                                                 


.. image:: /jupyter_notebooks/example_copernicus_files/example_copernicus_6_4.png


.. code-block:: python

    from greento.data.copernicus import copernicus
    from greento.boundingbox import boundingbox
    from greento.green.copernicus import copernicus as GreenCopernicus
    
    copernicus_downloader = copernicus(
            client_id="your_credential",
            client_secret="your_credential",
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            use_oidc=True
    )
    
    
    bbox = boundingbox()
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    
    copernicus_area = copernicus_downloader.get_data(bounding_box)
    copernicus_green = GreenCopernicus(copernicus_area)
    green_copernicus = copernicus_green.get_green()
    
    raster_data = green_copernicus["data"]
    
    # Plot the raster data
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    cmap_colors = ["white", "lightgreen", "green", "darkgreen", "black"]
    cmap = ListedColormap(cmap_colors[1:])
    plt.imshow(raster_data, cmap=cmap)
    plt.colorbar(label='Land Use Type')
    plt.title('Copernicus World Land Green Cover Data of the area')
    
    plt.show()


.. parsed-literal::

    Downloading Copernicus data:  20%|██        | 20/100 [00:01<00:07, 10.96it/s]

.. parsed-literal::

    Authenticated using refresh token.



.. image:: /jupyter_notebooks/example_copernicus_files/example_copernicus_7_3.png

