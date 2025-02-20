import osmnx as ox
import geopandas as gpd

class OSMDownloader:

    def get_vector_area(self, bounding_box, tags):
        aoi_box = bounding_box.to_geometry()

        try:
            polygon = aoi_box
            gdf = ox.features_from_polygon(polygon, tags)

            if not gdf.empty:
                # Clip the geometries to the AOI
                osm_area = gpd.clip(gdf, aoi_box)
                return osm_area
            return gdf

        except Exception as e:
            print(f"Error downloading OSM data: {str(e)}")
            raise

    def get_traffic_area(self, bounding_box, network_type):
        """
        Download the OSM network data for a given bounding box and network type, and rasterize it to a reference raster.
        """
        aoi_box = bounding_box.to_geometry()

        graph = ox.graph_from_polygon(aoi_box, network_type=network_type, simplify=True)

        if graph is None:
            print("Failed to create graph")
            return None

        # Convert graph to GeoDataFrames
        nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
        # Clip to AOI
        nodes = gpd.clip(nodes, aoi_box)
        edges = gpd.clip(edges, aoi_box)
        # Add coordinates
        nodes['x'] = nodes.geometry.x
        nodes['y'] = nodes.geometry.y

        if nodes.empty or edges.empty:
            print("Warning: Empty nodes or edges after processing")
            return None

        return (nodes, edges)
