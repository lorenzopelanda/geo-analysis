import rasterio
import tempfile
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
from data.CopernicusDownloader import CopernicusDownloader
from data.GHSPOPDownloader import GHSPOPDownloader

shapefile_path = "../tiling_schema/WGS84_tile_schema.shp"

class GHSPOPCopernicusMerged:
    def get_copernicus_population_area(self, bbox, address, use_oidc,copernicus_downloader,**kwargs):
        raster_data, copernicus_transform, copernicus_crs, copernicus_shape = copernicus_downloader.download_raster_area(
            bbox, use_oidc, **kwargs
        )
        ghs_pop = GHSPOPDownloader(address, shapefile_path)

        # Get Copernicus bounds
        copernicus_bounds = rasterio.transform.array_bounds(copernicus_shape[0], copernicus_shape[1],
                                                            copernicus_transform)

        # Get GHS-POP tiles
        tiles_gdf = self.load_shapefile()
        tiles_to_download = self.get_tiles_for_bounds(copernicus_bounds, tiles_gdf, ghs_pop)

        if not tiles_to_download:
            raise ValueError("No tiles to download for the given bounds.")

        ghspop_tiles = []
        for tile_id in tiles_to_download:
            zip_path = ghs_pop.download_tile(tile_id)
            if zip_path:
                tile_data = ghs_pop.extract_tif_file(zip_path)
                if tile_data is not None and tile_data.any():
                    # Ensure tile_data has the correct shape
                    # if len(tile_data.shape) == 2:
                    #     tile_data = tile_data[np.newaxis, :, :]
                    # elif len(tile_data.shape) > 3:
                    #     tile_data = np.squeeze(tile_data)
                    if len(tile_data.shape) == 4:
                        # Rimuovi la dimensione extra
                        tile_data = tile_data.squeeze()
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmpfile:
                        with rasterio.open(
                                tmpfile.name, 'w', driver='GTiff',
                                height=tile_data.shape[1], width=tile_data.shape[2],
                                count=1, dtype=tile_data.dtype, crs='EPSG:4326', transform=your_transform) as dst:
                            dst.write(tile_data, 1)
                        ghspop_tiles.append(tmpfile.name)
                else:
                    print(f"Failed to extract TIF file from {zip_path}")
            else:
                print(f"Failed to download tile {tile_id}")

        if not ghspop_tiles:
            raise ValueError("No GHS-POP tiles were downloaded or extracted successfully.")

        # Merge GHS-POP tiles
        if len(ghspop_tiles) == 1:
            ghs_data = ghspop_tiles[0]
            with rasterio.open(ghs_data) as src:
                ghs_transform = src.transform
                ghs_crs = src.crs
                ghs_shape = src.shape
        else:
            ghs_data, ghs_transform, ghs_crs, ghs_shape = self.merge_ghspop_tiles(ghspop_tiles)

        # Calculate the new transform for the Copernicus data
        ghs_bounds = rasterio.transform.array_bounds(ghs_shape[0], ghs_shape[1], ghs_transform)
        new_transform = from_bounds(*ghs_bounds, ghs_shape[1], ghs_shape[0])

        # Resample the Copernicus data to the GHS-POP resolution
        with rasterio.open(raster_data) as src:
            copernicus_resampled = src.read(
                out_shape=(src.count, ghs_shape[0], ghs_shape[1]),
                resampling=Resampling.average
            )
            copernicus_resampled = copernicus_resampled.squeeze()

        # Clip GHSPOP data to Copernicus extent
        copernicus_geometry = [box(*copernicus_bounds)]
        ghs_clipped, _ = mask(
             dataset=rasterio.open(ghs_data),
             shapes=copernicus_geometry,
            crop=True
        )
        copernicus_tif_path = "copernicus_resampled.tif"
        with rasterio.open(
                copernicus_tif_path,
                'w',
                driver='GTiff',
                height=copernicus_resampled.shape[0],
                width=copernicus_resampled.shape[1],
                count=1,
                dtype=copernicus_resampled.dtype,
                crs=copernicus_crs,
                transform=new_transform,
        ) as dst:
            dst.write(copernicus_resampled, 1)

        # Save GHSPOP clipped data to a .tif file
        ghs_tif_path = "ghspop_clipped.tif"
        with rasterio.open(
                ghs_tif_path,
                'w',
                driver='GTiff',
                height=ghs_clipped.shape[1],
                width=ghs_clipped.shape[2],
                count=1,
                dtype=ghs_clipped.dtype,
                crs=ghs_crs,
                transform=ghs_transform,
        ) as dst:
            dst.write(ghs_clipped[0], 1)

        # Update the Copernicus and GHSPOP data
        return {
            "copernicus": {
                "data": copernicus_resampled,
                "transform": new_transform,
                "crs": copernicus_crs,
                "shape": ghs_shape
            },
            "ghspop": {
                "data": ghs_clipped,
                "transform": ghs_transform,
                "crs": ghs_crs
            }
        }



    def load_shapefile(self):
        tiles_gdf = gpd.read_file(shapefile_path)
        if tiles_gdf.crs != "EPSG:4326":
            tiles_gdf = tiles_gdf.to_crs("EPSG:4326")
        print(f"Tiles CRS: {tiles_gdf.crs}")
        return tiles_gdf
    def create_point_gdf(self):
        point = Point(self.lat, self.lon)
        return gpd.GeoDataFrame([{'geometry': point}], crs="EPSG:4326")

    def get_tiles_for_bounds(self, bounds, tiles_gdf, ghs_pop):
        # Create a bounding box from the bounds
        bbox = box(bounds[0], bounds[1], bounds[2], bounds[3])
        bbox_gdf = gpd.GeoDataFrame([{'geometry': bbox}], crs="EPSG:4326")

        # Find intersecting tiles
        intersecting_tiles = tiles_gdf[tiles_gdf.intersects(bbox_gdf.geometry[0])]

        # Get tile IDs for intersecting tiles
        tile_ids = []
        for _, row in intersecting_tiles.iterrows():
            self.lat, self.lon = row.geometry.centroid.y, row.geometry.centroid.x
            point_gdf = self.create_point_gdf()
            tile_id = ghs_pop.get_tile_id(tiles_gdf, point_gdf)
            if tile_id:
                tile_ids.append(tile_id)

        return tile_ids

    def merge_ghspop_tiles(self, tiles):
        # List to store the opened datasets
        datasets = []

        for tile in tiles:
            # Open each tile and append to the datasets list
            datasets.append(rasterio.open(tile))

        # Merge the datasets
        mosaic, out_transform = merge(datasets)

        # Get the CRS and shape from the first dataset (assuming all tiles have the same CRS and shape)
        out_crs = datasets[0].crs
        out_shape = mosaic.shape[1:]

        # Close all datasets
        for dataset in datasets:
            dataset.close()
        return mosaic, out_transform, out_crs, out_shape

