import os
import shutil
import glob
import time

import geopandas as gpd
from pyproj import CRS
import earthpy.clip as ec
from osgeo import ogr

import logging

ogr.UseExceptions()

TEST_CLIP_EXTENT = r"/Volumes/W0425931/_data/geonova/20200115/Digby/BrierIsland.shp"
TEST_SHAPE_FILE_DIRECTORY = r"/Volumes/W0425931/_cogs/5_Winter_2020/CART4032_Digby/data/geonova/Selected Shapefiles"
TEST_SHAPE_FILES = glob.glob(os.path.join(TEST_SHAPE_FILE_DIRECTORY, "*.shp"))
TEST_OUTPUT_PATH = r"/Users/thozub/_projects/data-prep/output"


def init_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s %(message)s')


def check_geometries(data_frame):
    data_frame["is_valid"] = data_frame["geometry"].is_valid

    valid_values = data_frame.loc[data_frame["is_valid"]]
    non_valid_values = data_frame.loc[data_frame["is_valid"] == False]

    return valid_values, non_valid_values


def fix_polygons(data_frame):
    """ Fixes ring self intersected polygons by applying a buffer of 0. Returns the data frame enriched with an
        additional column indicating if geometries are valid or not an a data frame only containing features
        with invalid geometries will be returned as well. """
    data_frame["geometry"] = data_frame["geometry"].buffer(0.0)


def is_polygon_feature_set(data_frame):
    """ Returns true if the given data frame contains polygons. """
    return data_frame.loc[0, "geometry"] == "Polygon"


def project_data_frame(data_frame, epsg_code):
    crs = CRS.from_epsg(epsg_code).to_wkt()
    data_frame = data_frame.to_crs(crs)
    return data_frame


class ExecutionTimer:

    def __init__(self):
        self.start_time = None
        self.reset()

    def get_running_time(self):
        return time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()

    def log_running_time(self):
        logging.info("Execution time: {0:.0f} seconds".format(self.get_running_time()))


class ShapeFileClipperLog:

    def __init__(self, result_message, ignored_values, execution_time):
        self.result_message = result_message
        self.ignored_values = ignored_values
        self.execution_time = execution_time

    def __repr__(self):

        if self.ignored_values is None or len(self.ignored_values) == 0:
            return "{}\nExecution Time: {}".format(self.result_message, self.execution_time)

        return "{}\nIgnored (invalid) Values:\n{}\nExecution Time: {}".format(
            self.result_message, self.ignored_values, self.execution_time)


class ShapeFileClipper:

    def __init__(self, clip_shape_file, output_path, output_file_postfix):
        self.clip_extent = gpd.read_file(clip_shape_file)
        self.output_path = output_path
        self.output_file_postfix = output_file_postfix
        self.log = []

    def __generate_clipped_output_file_path(self, file_path):
        name, extension = os.path.splitext(os.path.basename(file_path))
        new_file_name = "".join([name, self.output_file_postfix, extension])
        if self.output_path is None:
            return os.path.join(os.path.dirname(file_path), new_file_name)
        return os.path.join(self.output_path, new_file_name)

    def __clip_data(self, data_frame):
        clipped_data_frame = ec.clip_shp(data_frame, self.clip_extent)
        clipped_data_frame.crs = data_frame.crs
        return clipped_data_frame[~clipped_data_frame.is_empty]

    def __clip(self, shape_file):

        # load shape file
        data_frame = gpd.read_file(shape_file)

        shape_file_name = os.path.basename(shape_file)

        # fix invalid polygons
        if is_polygon_feature_set(data_frame):
            fix_polygons(data_frame)

        # check geometries and enrich with column is_valid
        valid_values, non_valid_values = check_geometries(data_frame)

        if not any(valid_values.intersects(self.clip_extent.unary_union)):
            return None, non_valid_values, "{} does not overlap with clipping extent. Ignored.".format(shape_file_name)

        clipped_data_frame = self.__clip_data(valid_values)

        if len(clipped_data_frame) == 0:
            return None, non_valid_values, "No features of {} within clipping extent.".format(shape_file_name)

        return clipped_data_frame, non_valid_values, "{} successfully clipped.".format(shape_file_name)

    def __save_shape_file(self, data_frame, shape_file):
        output_file_path = self.__generate_clipped_output_file_path(shape_file)
        data_frame.to_file(driver="ESRI Shapefile", filename=output_file_path, encoding="UTF-8")
        return output_file_path

    def clip(self, shape_file):

        timer = ExecutionTimer()

        clipped_data_frame, ignored_values, result_message = self.__clip(shape_file)

        self.log.append(ShapeFileClipperLog(result_message, ignored_values, timer.get_running_time()))
        timer.reset()

        if clipped_data_frame is not None:

            output_file_path = self.__save_shape_file(clipped_data_frame, shape_file)

            result_message = "{} saved.".format(output_file_path)
            self.log.append(ShapeFileClipperLog(result_message, None, timer.get_running_time()))

    def clip_and_project(self, shape_file, epsg_code):

        timer = ExecutionTimer()

        clipped_data_frame, ignored_values, result_message = self.__clip(shape_file)

        self.log.append(ShapeFileClipperLog(result_message, ignored_values, timer.get_running_time()))
        timer.reset()

        if clipped_data_frame is not None:

            clipped_data_frame = project_data_frame(clipped_data_frame, epsg_code)
            output_file_path = self.__save_shape_file(clipped_data_frame, shape_file)

            result_message = "{} projected and saved.".format(output_file_path)
            self.log.append(ShapeFileClipperLog(result_message, None, timer.get_running_time()))

    def print_log(self):
        for log_entry in self.log:
            print(log_entry)


def clip_and_project(shape_files, clip_shape_file, output_path, output_file_postfix, epsg_code):
    clipper = ShapeFileClipper(clip_shape_file, output_path, output_file_postfix)
    for shape_file in shape_files:
        clipper.clip_and_project(shape_file, epsg_code)
    clipper.print_log()


def run_test():

    # clear output directory
    shutil.rmtree(TEST_OUTPUT_PATH, ignore_errors=True)
    os.mkdir(TEST_OUTPUT_PATH)

    init_logging()
    timer = ExecutionTimer()
    clip_and_project(TEST_SHAPE_FILES, TEST_CLIP_EXTENT, TEST_OUTPUT_PATH, "_clipped", 2961)
    timer.log_running_time()


if __name__ == '__main__':
    run_test()

