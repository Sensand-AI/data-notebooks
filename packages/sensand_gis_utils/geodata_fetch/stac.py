from odc.stac import stac_load
from pystac_client import Client


class base_image_collection:
    """
    Base object for ImageCollection objects.
    """
    def __init__(self, collection):
        self.collection = collection
        self.datetime = None
        self.geometry = None

    def filter_date(self, start_date, end_date):
        self.datetime = f"{start_date}/{end_date}"
        return self

    def filter_bounds(self, geometry):
        self.geometry = geometry
        return self

    def _search(self, url, parameters=None):
        client = Client.open(url)

        search = client.search(
            bbox=self.geometry,
            datetime=self.datetime,
            collections=self.collection  # this is for searching one STAC collection at a time
        )
        return search


class image_collection(base_image_collection):
    def from_STAC(self, url):
        """
        Initialise the STAC query

        Parameters:
        url: the STAC catalog url used to search for the items

        Returns:
        an image_collection object
        """
        self.stac = url
        return self

    def get_info(self, **kwargs):
        """
        Return all information from the STAC search

        Parameters:
        **kwargs: additional arguments passed to stackstac.stack() e.g. epsg, resolution, bbox

        Returns:
        xarray.DataArray: The stacked image collection
        """
        query = self._search(url=self.stac)
        items = [item.to_dict() for item in query.get_items()]

        img_collection = stac_load(items, **kwargs)

        # this loads the data into local memory:
        img_collection = img_collection.compute()

        return img_collection
