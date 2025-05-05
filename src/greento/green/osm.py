import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from .interface import interface

class osm(interface):
    """
    A class to process green areas using OpenStreetMap (OSM) data.

    Attributes
    ----------
    osm : tuple
        A tuple containing two GeoDataFrames: nodes and edges.

    Methods
    -------
    get_green(**kwargs) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        Filters and processes green areas from the OSM data.
    """
    def __init__(self, osm) -> None:
        """
        Initializes the GreenOSM class with OSM data.

        Parameters
        ----------
        osm : tuple
            A tuple containing two GeoDataFrames: nodes and edges.

        Returns
        -------
        None
        """
        self.osm = osm    
    
    def get_green(self, **kwargs) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Filters and processes green areas from the OSM data.

        Parameters
        ----------
        **kwargs : dict, optional
            Additional arguments to specify green tags.
            - green_tags (dict, optional): A dictionary of tags to filter green areas. 
              Default is:
              {
                  'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
                              'heath', 'fell', 'tundra', 'shrubbery'],
                  'landuse': ['forest', 'meadow', 'grass', 'allotments'],
                  'leisure': ['park', 'garden', 'nature_reserve']
              }

        Returns
        -------
        tuple
            A tuple containing two GeoDataFrames:
            - green_nodes (geopandas.GeoDataFrame): Filtered green nodes.
            - green_edges (geopandas.GeoDataFrame): Filtered green edges.

        Raises
        ------
        Exception
            If an error occurs during processing, returns empty GeoDataFrames.

        Notes
        -----
        The method uses the `pandas` and `geopandas` libraries to filter OSM data based on specified tags.
        """
        
        try:
            nodes_gdf, edges_gdf = self.osm
            if kwargs is None:
                green_tags = {
                    'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
                            'heath', 'fell', 'tundra', 'shrubbery'],
                    'landuse': ['forest', 'meadow', 'grass','allotments'],
                    'leisure': ['park', 'garden', 'nature_reserve']
                }
            else:
                green_tags = kwargs.get('green_tags', {
                    'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
                            'heath', 'fell', 'tundra', 'shrubbery'],
                    'landuse': ['forest', 'meadow', 'grass','allotments'],
                    'leisure': ['park', 'garden', 'nature_reserve']
                })

            def filter_green(df):
                if df.empty:
                    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(), crs=df.crs if hasattr(df, 'crs') else None)

                mask = pd.Series(False, index=df.index)

                for tag, values in green_tags.items():
                    if tag in df.columns:
                        mask |= df[tag].isin(values)
                
                if not mask.any():
                    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(), crs=df.crs if hasattr(df, 'crs') else None)
                
                return df[mask]  

            green_nodes = gpd.GeoDataFrame(geometry=gpd.GeoSeries())
            green_edges = gpd.GeoDataFrame(geometry=gpd.GeoSeries())

            for df, name in tqdm([(nodes_gdf, 'nodes'), (edges_gdf, 'edges')], desc="Filtering OSM green areas", leave=False):
                if name == 'nodes':
                    green_nodes = filter_green(df)
                else:
                    green_edges = filter_green(df)
            
            return (green_nodes, green_edges)

        except Exception as e:
            empty_geo = gpd.GeoDataFrame(geometry=gpd.GeoSeries())
            return (empty_geo, empty_geo)
