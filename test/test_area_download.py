import os
os.environ["PROJ_LIB"] = "/home/lorenzo/miniconda3/envs/geodata_env/share/proj"
from data.boundingbox.BoundingBox import BoundingBox
from data.downloader.CopernicusDownloader import CopernicusDownloader
from data.utils.LandUtils import LandUtils
from data.downloader.GHSPOPDownloader import GHSPOPDownloader
from data.downloader.OSMDownloader import OSMDownloader


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
    bounding_box = bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    #
    copernicus_area = copernicus_downloader.download_raster_area(
        bounding_box,
        use_oidc=False
    )

    # ghs_pop = GHSPOPDownloader(
    #     address="Piazza Castello, Torino"
    # )
    # ghspop_area = ghs_pop.get_population_area(bounding_box_instance)
    #

    #
    osm_area = OSMDownloader()
    osm_area_traffic = osm_area.get_traffic_area(
        bounding_box=bounding_box,
        network_type="all_public"
    )
    detail_adjuster = LandUtils()
    detail_adjuster.vector_to_raster(osm_area_traffic, copernicus_area)
    #osm_bus = osm_area.get_traffic_area(bounding_box=bounding_box, network_type ="all_public", reference_raster=copernicus_area)

    #osm_building_raster = detail_adjuster.vector_to_raster(osm_area_building, copernicus_area)





if __name__ == "__main__":
    main()

