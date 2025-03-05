import os
import json
os.environ["PROJ_LIB"] = "/home/lorenzo/miniconda3/envs/geodata_env/share/proj"
from data.boundingbox.BoundingBox import BoundingBox
from data.downloader.CopernicusDownloader import CopernicusDownloader
from data.utils.LandUseAnalyzer import LandUseAnalyzer
from data.utils.LandUtils import LandUtils
from data.utils.BoundingBoxUtils import BoundingBoxUtils
from data.utils.GreenAreaFinder import GreenAreaFinder
from data.downloader.OSMDownloader import OSMDownloader
from data.downloader.GHSPOPDownloader import GHSPOPDownloader


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
    osm_area = OSMDownloader()
    osm_area = osm_area.get_traffic_area(
        bounding_box=bounding_box,
        network_type="walk"
    )

    ghspop = GHSPOPDownloader(
        address="Piazza Castello, Torino",
        shapefile="../tiling_schema/WGS84_tile_schema.shp"
    )
    ghspop_area = ghspop.get_population_area(bounding_box)
    ghs_pop_resized = LandUtils().adjust_detail_level(copernicus_area, ghspop_area)
    #address = "Via Antonio Bertola 48/C, Torino"
    #lat, lon = LandUtils().get_coordinates_from_address(address)

    #lat, lon = 45.071526, 7.681753 #Via Barbaroux 12, Torino
    lat, lon = 45.072710, 7.679646
    print(f"Coordinates for the starting point: {lat}, {lon}")
    #lat,lon = 45.085309, 7.631144

    green_area_finder = GreenAreaFinder(
        copernicus_area,
        osm_area,
        ghs_pop_resized,
    )

    # population_green_ratio = green_area_finder.green_area_per_person()
    # print(f"Green area / population: {population_green_ratio}")

    # isochrone_area = green_area_finder.get_isochrone_green(lat, lon, 12, "walk")
    # print("Raw output:", isochrone_area)  # Stampa l'output prima della conversione
    # isochrone_area = json.loads(isochrone_area)
    # print("Parsed JSON:", isochrone_area)  # Stampa il dizionario convertito
    # time = isochrone_area.get("isochrone_time_minutes")  # Usa .get() per evitare KeyError
    # print("Time:", time)
    # green_area_percentage = isochrone_area["green_area_percentage"]
    # areasq = isochrone_area["green_area_sqm"]
    # print(f"Time max to reach the green area: {time} minutes")
    # print(f"Green area percentage: {green_area_percentage}%")
    # print(f"Green area in sqm walked: {areasq} sqm")

    #latitude, longitude = LandUtils().get_coordinates_max_population(ghs_pop_resized)
    # print(f"Coordinates with the highest number of people: {latitude}, {longitude}")
    distance = green_area_finder.direction_to_green(lat, lon, "walk")
    distance = json.loads(distance)
    minute = distance['estimated_time_minutes']
    distance_km = distance['distance_km']
    print(f"Estimated time to the nearest green area: {minute} minutes")
    print(f"Distance to the nearest green area: {distance_km} km")

    #raster_data_ESRI54009 = LandUtils().transform_raster_to_crs(copernicus_area['data'],copernicus_area['transform'], copernicus_area['crs'],copernicus_area['shape'], "ESRI:54009")
    #print(raster_data_ESRI54009['crs'])
    # landuse_analyzer = LandUseAnalyzer(copernicus_area)
    # print(landuse_analyzer.get_land_use_percentages())


if __name__ == "__main__":
    main()