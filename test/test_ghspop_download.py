from data.GHSPOPDownloader import GHSPOPDownloader
def main():
    address = "Washington, D.C., USA"
    shapefile_path = "../tiling_schema/WGS84_tile_schema.shp"
    downloader = GHSPOPDownloader(address, shapefile_path)
    downloader.get_population_area()

if __name__ == "__main__":
    main()

