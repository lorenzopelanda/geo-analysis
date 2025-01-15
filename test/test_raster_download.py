from data.RasterDownloader import RasterDownloader

def main():
    downloader = RasterDownloader(
        client_id = "sh-a24a739d-d123-419b-a409-81a190c436c2",
        client_secret = "dcUnE32uBB1gLvlxyi3qOeUPdGGpNMRs",
        token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    )

    downloader.download_raster_area(
        query="Piazza Castello, Torino",
        travel_time=0,
        travel_mode="walk",
        use_oidc=False
    )


if __name__ == "__main__":
    main()

