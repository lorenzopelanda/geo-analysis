import os
os.environ["PROJ_LIB"] = "/home/lorenzo/miniconda3/envs/geodata_env/share/proj"
from data.boundingbox.BoundingBox import BoundingBox
from data.downloader.CopernicusDownloader import CopernicusDownloader
from data.utils.LandUseAnalyzer import LandUseAnalyzer
from data.utils.LandUtils import LandUtils
from data.utils.BoundingBoxUtils import BoundingBoxUtils


def main():
    copernicus_downloader = CopernicusDownloader(
        client_id="sh-a24a739d-d123-419b-a409-81a190c436c2",
        client_secret="dcUnE32uBB1gLvlxyi3qOeUPdGGpNMRs",
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    )
    bbox = BoundingBox()
    bounding_box= bbox.get_bounding_box(query="Piazza Castello, Torino", method="from_center_radius", radius_km=15)



    copernicus_area= copernicus_downloader.download_raster_area(
         bounding_box,
         use_oidc=False
    )


    raster_data_ESRI54009 = LandUtils().transform_raster_to_crs(copernicus_area['data'],copernicus_area['transform'], copernicus_area['crs'],copernicus_area['shape'], "ESRI:54009")
    print(raster_data_ESRI54009['crs'])
    # landuse_analyzer = LandUseAnalyzer(copernicus_area)
    # print(landuse_analyzer.get_land_use_percentages())


if __name__ == "__main__":
    main()