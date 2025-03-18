import pandas as pd
from tqdm import tqdm
from .GreenInterface import GreenInterface

class GreenOSM(GreenInterface):
    def __init__(self, osm):
        self.osm = osm    
    # def get_green(self, **kwargs):
    #     try:
    #         nodes_gdf, edges_gdf = self.osm
    #         if kwargs is None:
    #             green_tags = {
    #                 'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
    #                             'heath', 'fell', 'tundra', 'shrubbery'],
    #                 'landuse': ['forest', 'meadow', 'grass','allotments'],
    #                 'leisure': ['park', 'garden', 'nature_reserve']
    #             }
    #         else :
    #             green_tags = kwargs.get('green_tags', {
    #                 'natural': ['wood', 'tree_row', 'tree', 'scrub', 'grassland',
    #                             'heath', 'fell', 'tundra', 'shrubbery'],
    #                 'landuse': ['forest', 'meadow', 'grass','allotments'],
    #                 'leisure': ['park', 'garden', 'nature_reserve']
    #             })

    #         def filter_green(df):
    #             if df.empty:
    #                 return df

    #             mask = pd.Series(False, index=df.index)

    #             for tag, values in green_tags.items():
    #                 if tag in df.columns:
    #                     mask |= df[tag].isin(values)

    #             return df[mask]

    #         # Optimized filtering
    #         green_nodes = filter_green(nodes_gdf)
    #         green_edges = filter_green(edges_gdf)


    #         return (green_nodes, green_edges)

    #     except Exception as e:
    #         return (pd.DataFrame(), pd.DataFrame())

    def get_green(self, **kwargs):
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
                    return df

                mask = pd.Series(False, index=df.index)

                for tag, values in green_tags.items():
                    if tag in df.columns:
                        mask |= df[tag].isin(values)

                return df[mask]

            # Optimized filtering with progress bar
            green_nodes = pd.DataFrame()
            green_edges = pd.DataFrame()

            for df, name in tqdm([(nodes_gdf, 'nodes'), (edges_gdf, 'edges')], desc="Filtering OSM green areas"):
                if name == 'nodes':
                    green_nodes = filter_green(df)
                else:
                    green_edges = filter_green(df)

            return (green_nodes, green_edges)

        except Exception as e:
            return (pd.DataFrame(), pd.DataFrame())
