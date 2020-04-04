from pyproj import CRS
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon


def check_geometries(data_frame):
    """ Checks the geometry of each feature and returns two data frames, one with all valid values
        and a second one with the invalid features. """

    # enrich data_frame with an is_valid column to avoid a second, redundant validation
    # for both data_frames
    data_frame["is_valid"] = data_frame["geometry"].is_valid

    valid_values = data_frame.loc[data_frame["is_valid"]]
    non_valid_values = data_frame.loc[data_frame["is_valid"] == False]

    return valid_values, non_valid_values


def fix_polygons(data_frame):
    """ Fixes ring self intersected polygons by applying a buffer of 0. Returns the data frame
        enriched with an additional column indicating if geometries are valid or not an a data
        frame only containing features with invalid geometries will be returned as well. """

    data_frame["geometry"] = data_frame["geometry"].buffer(0.0)
    return data_frame


def is_polygon_feature_set(data_frame, include_multipolygons=True):
    """ Returns true if the given data frame contains polygons or multi-polygons. """

    if include_multipolygons and isinstance(data_frame.loc[0, "geometry"], MultiPolygon):
        return True
    return isinstance(data_frame.loc[0, "geometry"], Polygon)


def project_data_frame(data_frame, epsg_code):
    """ Re-project given data frame using given EPSG code. Returns the
        reprojected data frame. """

    crs = CRS.from_epsg(epsg_code).to_wkt()
    data_frame = data_frame.to_crs(crs)
    return data_frame
