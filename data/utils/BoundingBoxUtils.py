import pyproj
from pyproj import CRS, Transformer
from data.boundingbox.BoundingBox import BoundingBox

class BoundingBoxUtils:
    def transform_to_crs(self, bounding_box, dst_crs):
        """
        Transform the given bounding box to the specified CRS.
        """
        if bounding_box.polygon is None:
            bounding_box.polygon = bounding_box.to_geometry()

        crs_src = pyproj.CRS.from_string(bounding_box.crs)
        crs_dest = pyproj.CRS.from_string(dst_crs)
        transformer = Transformer.from_crs(crs_src, crs_dest, always_xy=True)
        min_x, min_y = transformer.transform(bounding_box.min_x, bounding_box.min_y)
        max_x, max_y = transformer.transform(bounding_box.max_x, bounding_box.max_y)

        result = BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, crs=dst_crs)
        result.polygon = result.to_geometry()
        return result
