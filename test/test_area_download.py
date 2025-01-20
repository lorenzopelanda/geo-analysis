from data.BoundingBox import BoundingBox
from data.CopernicusDownloader import CopernicusDownloader
from data.GHSPOPCopernicusMerged import GHSPOPCopernicusMerged
from data.OSMDownloader import OSMDownloader


def main():
    copernicus_downloader = CopernicusDownloader(
        client_id="sh-a24a739d-d123-419b-a409-81a190c436c2",
        client_secret="dcUnE32uBB1gLvlxyi3qOeUPdGGpNMRs",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    )

    bbox = BoundingBox()
    bbox= bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)
    downloader_raster = GHSPOPCopernicusMerged()
    downloader_raster.get_copernicus_population_area(
        bbox=bbox,
        address="Piazza Castello, Torino",
        use_oidc=False,
        copernicus_downloader=copernicus_downloader,
    )

    # osm_area = OSMDownloader()
    # osm_area.get_vector_area(bounding_box=bbox, tags={"building": True})

    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=10)
    #
    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_coordinates", min_x=7.68, min_y=45.06, max_x=7.70, max_y=45.08)
    #
    # geojson_data = '{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[7.68, 45.06], [7.70, 45.06], [7.70, 45.08], [7.68, 45.08], [7.68, 45.06]]]}}'
    # bbox = get_bounding_box(query="Piazza Castello, Torino", method="from_geojson", geojson=geojson_data)

if __name__ == "__main__":
    main()

