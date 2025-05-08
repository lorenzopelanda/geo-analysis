import logging
import os
import shutil
import zipfile
from typing import List, Optional

import requests


class ghspop_io:
    """
    A class to manage downloading, extracting, and cleaning up GHS-POP data files.

    Methods
    -------
    __download_tile(tile_id: str) -> str
        Downloads a GHS-POP tile as a ZIP file from the specified URL.
    __extract_tif_file(zip_path: str) -> str
        Extracts the TIF file from a downloaded ZIP file.
    __cleanup_files(file_paths: List[str]) -> None
        Cleans up temporary files and directories created during processing.
    """

    def __init__(self, extracted_dir: str = "extracted_files") -> None:
        """
        Initializes the GHS-POP IO class with a directory for extracted files.

        Parameters
        ----------
        extracted_dir : str
            The directory where extracted files will be stored.

        Returns
        -------
        None
        """
        self.extracted_dir = extracted_dir

    def _download_tile(self, tile_id: str) -> Optional[str]:
        """
        Downloads a GHS-POP tile as a ZIP file from the specified URL.

        Parameters
        ----------
        tile_id : str
            The ID of the tile to download.

        Returns
        -------
        str
            The path to the downloaded ZIP file, or None if the download fails.
        """
        url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0_{tile_id}.zip"
        response = requests.get(url)
        if response.status_code == 200:
            zip_path = "tile_download.zip"
            with open(zip_path, "wb") as file:
                file.write(response.content)
            return zip_path
        return None

    def _extract_tif_file(self, zip_path: str) -> Optional[str]:
        """
        Extracts the TIF file from a downloaded ZIP file.

        Parameters
        ----------
        zip_path : str
            The path to the ZIP file to extract.

        Returns
        -------
        str
            The path to the extracted TIF file, or None if extraction fails.

        Raises
        ------
        Exception
            If an error occurs during the extraction process.
        """
        logger = logging.getLogger(__name__)
        tif_path = None
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(".tif"):
                        zip_ref.extract(file, self.extracted_dir)
                        tif_path = os.path.join(self.extracted_dir, file)
                        if not os.path.exists(tif_path):
                            tif_path = None
                        break

            if os.path.exists(zip_path):
                os.remove(zip_path)

            return tif_path

        except Exception as e:
            logger.error(f"Error during TIF extraction: {str(e)}")
            return None

    def __cleanup_files(self, file_paths: List[str]) -> None:
        """
        Cleans up temporary files and directories created during processing.

        Parameters
        ----------
        file_paths : list of str
            A list of file paths to remove.

        Returns
        -------
        None

        Raises
        ------
        Exception
            If an error occurs while removing files or directories.
        """
        logger = logging.getLogger(__name__)
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.error(f"Error removing file {path}: {str(e)}")
                return None

        try:
            if os.path.exists(self.extracted_dir) and not os.listdir(
                self.extracted_dir
            ):
                shutil.rmtree(self.extracted_dir)
        except Exception as e:
            logger.error(f"Error removing directory {self.extracted_dir}: {str(e)}")
            return None
