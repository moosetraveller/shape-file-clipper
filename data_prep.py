import os
import shutil
import glob
import time

import geopandas as gpd
from pyproj import CRS
import earthpy.clip as ec
from osgeo import ogr

import logging

start_time = time.time()

ogr.UseExceptions()

path = os.path.dirname(os.path.abspath(__file__))

bbox_file = r"/Volumes/W0425931/_data/geonova/20200115/Digby/BrierIsland.shp"
# bbox_file = os.path.join(path, "test", "bbox.shp")

data_path = r"/Volumes/W0425931/_cogs/5_Winter_2020/CART4032_Digby/data/geonova/Selected Shapefiles"
# data_path = os.path.join(path, "data")

output_path = os.path.join(path, "output")

shutil.rmtree(output_path, ignore_errors=True)
os.mkdir(output_path)

shape_files = glob.glob(os.path.join(data_path, "*.shp"))

bbox = gpd.read_file(bbox_file)


def init_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s %(message)s')


init_logging()


# class ShapeFileClipper():
#
#     def __init__(self, bbox):
#         self.bbox = bbox
#         pass


def get_clipped_file_name(file_path, output_path=None, postfix="_clipped"):
    name, extension = os.path.splitext(os.path.basename(file_path))
    new_file_name = "".join([name, postfix, extension])
    if output_path is None:
        return os.path.join(os.path.dirname(file_path), new_file_name)
    return os.path.join(output_path, new_file_name)


def clip_data(data_frame, bbox):
    clipped_data_frame = ec.clip_shp(data_frame, bbox)
    clipped_data_frame.crs = data_frame.crs
    return clipped_data_frame[~clipped_data_frame.is_empty]


def project_data_frame(data_frame, epsg_code):
    crs = CRS.from_epsg(epsg_code).to_wkt()
    data_frame = data_frame.to_crs(crs)
    return data_frame


def fix_ring_self_intersected_polygon(data_frame):
    data_frame["geometry"] = data_frame["geometry"].buffer(0.0)  # https://stackoverflow.com/questions/11894149/automatically-fixing-ring-self-intersections-in-shp2pgsql
    data_frame["is_valid"] = data_frame["geometry"].is_valid
    non_valid_values = data_frame.loc[data_frame["is_valid"] == False]
    return data_frame, non_valid_values


def clip_shape_file(shape_file, bbox, output_path=None, output_file_postfix="_clipped", skip_empty=True, do_project_clipped_data=False, epsg_code=None):
    data_frame = gpd.read_file(shape_file)
    geom_type = data_frame.loc[0, "geometry"]
    if geom_type == "Polygon":
        data_frame, non_valid_values = fix_ring_self_intersected_polygon(data_frame)
        logging.info("{} invalid polygons found.".format(len(non_valid_values)))
    else:
        data_frame["is_valid"] = data_frame["geometry"].is_valid
    data_frame = data_frame.loc[data_frame["is_valid"]]
    if not any(data_frame.intersects(bbox.unary_union)):
        logging.info("{} does not overlap with crop extent.".format(shape_file))
        return
    clipped_data_frame = clip_data(data_frame, bbox)
    if do_project_clipped_data:
        clipped_data_frame = project_data_frame(clipped_data_frame, epsg_code)
    if skip_empty and len(clipped_data_frame) == 0:
        logging.info("{} skipped. No data in clipped area.".format(shape_file))
        return
    output_fp = get_clipped_file_name(shape_file, output_path=output_path, postfix=output_file_postfix)
    clipped_data_frame.to_file(driver="ESRI Shapefile", filename=output_fp, encoding="UTF-8")


for shape_file in shape_files:
    logging.info("Processing {}...".format(shape_file))
    clip_shape_file(shape_file, bbox, output_path=output_path, do_project_clipped_data=True, epsg_code=2961)

logging.info("Execution time: {0:.0f} seconds".format((time.time() - start_time)))



# driver = ogr.GetDriverByName("ESRI Shapefile")
#
# for shape_file in shape_files:
#     data_source = driver.Open(shape_file, 0)
#     layer = data_source.GetLayer()
#     layer_def = layer.GetLayerDefn()
#     for index, field_def in [(index, layer_def.GetFieldDefn(index)) for index in range(layer_def.GetFieldCount())]:
#         print(index, field_def.GetName())
