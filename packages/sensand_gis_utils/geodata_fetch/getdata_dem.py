import json
import logging
import os
from importlib import resources

from owslib.wcs import WebCoverageService

from geodata_fetch.utils import retry_decorator

logger = logging.getLogger()
# try this but remove if it doesn't work well with datadog:
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BaseHarvest:
    def __init__(self, config_filename):
        try:
            with resources.open_text("data", config_filename) as f:
                config_json = json.load(f)
            self.initialise_attributes_from_json(config_json)
        except Exception as e:
            logger.error(
                f"Error loading {config_filename} to {self.__class__.__name__} module.",
                exec_info=True,
            )
            raise ValueError(
                f"Error loading {config_filename} to {self.__class__.__name__} module: {e}"
            ) from e

    def initialise_attributes_from_json(self, config_json):
        self.title = config_json.get("title")
        self.description = config_json.get("description")
        self.license = config_json.get("license")
        self.source_url = config_json.get("source_url")
        self.copyright = config_json.get("copyright")
        self.attribution = config_json.get("attribution")
        self.crs = config_json.get("crs")
        self.bbox = config_json.get("bbox")
        self.resolution_arcsec = config_json.get("resolution_arcsec")
        self.layers_url = config_json.get("layers_url")
        self.fetched_files = []


class dem_harvest(BaseHarvest):
    def __init__(self):
        super().__init__("dem.json")

    @retry_decorator()
    def getwcs_dem(self, url, crs, resolution, bbox, property_name, outpath):
        """
        Downloads a Digital Elevation Model (DEM) using the Web Coverage Service (WCS) protocol.

        Args:
            url (str): The URL of the WCS server.
            crs (str): The coordinate reference system (CRS) of the requested data.
            resolution (float): The resolution of the requested data in arcseconds.
            bbox (tuple): The bounding box of the requested data in the format (minx, miny, maxx, maxy).
            property_name (str): The name of the property associated with the DEM.
            outpath (str): The output directory where the downloaded DEM will be saved.

        Returns:
            str: The filepath of the downloaded DEM.

        Raises:
            ServiceException: If the WCS server returns an exception.
            HTTPError: If there is an HTTP error while accessing the WCS server.
            Exception: If there is a general error while downloading the DEM.

        """
        try:
            if resolution is None:
                resolution = self.resolution_arcsec

            wcs = WebCoverageService(url, version="1.0.0", timeout=600)
            # layername is handled differently here compared to SLGA due to structure of the endpoint
            layername = wcs["1"].title
            fname_out = layername.replace(" ", "_") + "_" + property_name + ".tiff"
            outfname = os.path.join(outpath, fname_out)

            print(outfname)

            os.makedirs(outpath, exist_ok=True)

            data = wcs.getCoverage(
                identifier="1",
                bbox=bbox,
                format="GeoTIFF",
                crs=crs,
                resx=resolution,
                resy=resolution,
            )

            with open(outfname, "wb") as f:
                f.write(data.read())
                logger.info(f"WCS data downloaded and saved as {fname_out}")

        except Exception as e:
            if e.response.status_code == 502:
                logger.error(
                    f"HTTPError 502: Bad Gateway encountered when accessing {url}",
                    exec_info=True,
                )
            elif e.response.status_code == 503:
                logger.error(
                    f"HTTPError 503: Service Unavailable encountered when accessing {url}",
                    exec_info=True,
                )
            else:
                logger.error(
                    f"Error {e.response.status_code}: {e.response.reason} when accessing {url}",
                    exec_info=True,
                )
        return outfname

    def get_dem_layers(self, property_name, layernames, bbox, outpath):
        """
        Fetches DEM layers based on the provided parameters.

        Args:
            property_name (str): The name of the property.
            layernames (str or list): The name(s) of the DEM layer(s) to fetch.
            bbox (tuple): The bounding box coordinates (xmin, ymin, xmax, ymax).
            outpath (str): The output path to save the fetched layers.

        Returns:
            list: A list of file names of the fetched DEM layers.

        Raises:
            Exception: If there is an error while fetching the DEM layers.

        """
        try:
            if not isinstance(layernames, list):
                layernames = [layernames]

            os.makedirs(outpath, exist_ok=True)

            fnames_out = []
            for layername in layernames:
                if layername == "DEM":
                    outfname = self.getwcs_dem(
                        url=self.layers_url["DEM"],
                        crs=self.crs,
                        resolution=self.resolution_arcsec,
                        bbox=bbox,
                        property_name=property_name,
                        outpath=outpath,
                    )
                    if outfname:
                        fnames_out.append(outfname)

            return fnames_out
        except Exception as e:
            logger.error(
                "Failed to get DEM layers",
                exc_info=True,
                extra={"layernames": layernames, "error": str(e)},
            )
            return None


class dem_harves_global(BaseHarvest):
    def __init__(self):
        super().__init__("stac_dem.json")
