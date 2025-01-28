import os
os.environ["PROJ_LIB"] = "/home/lorenzo/miniconda3/envs/geodata_env/share/proj"
from data.BoundingBox import BoundingBox
from data.CopernicusDownloader import CopernicusDownloader
from data.DetailLevelAdjustment import DetailLevelAdjustment
from data.GHSPOPDownloader import GHSPOPDownloader
from data.OSMDownloader import OSMDownloader


def main():
    copernicus_downloader = CopernicusDownloader(
        client_id="sh-a24a739d-d123-419b-a409-81a190c436c2",
        client_secret="dcUnE32uBB1gLvlxyi3qOeUPdGGpNMRs",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    )

    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=10)
    #
    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_coordinates", min_x=7.68, min_y=45.06, max_x=7.70, max_y=45.08)
    #
    # geojson_data = '{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[7.68, 45.06], [7.70, 45.06], [7.70, 45.08], [7.68, 45.08], [7.68, 45.06]]]}}'
    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_geojson", geojson=geojson_data)
    bbox = BoundingBox()
    bounding_box= bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)

    copernicus_area = copernicus_downloader.download_raster_area(
         bounding_box,
         use_oidc=False
    )

    ghs_pop = GHSPOPDownloader(
        address="Piazza Castello, Torino",
        shapefile_path="../tiling_schema/WGS84_tile_schema.shp"
    )
    ghspop_area = ghs_pop.get_population_area(bounding_box)

    detail_adjuster = DetailLevelAdjustment()
    detail_adjuster.adjust_detail_level(copernicus_area, ghspop_area)

    osm_area = OSMDownloader()
    osm_area.get_vector_area(bounding_box=bbox, tags={"building": True})



if __name__ == "__main__":
    main()

