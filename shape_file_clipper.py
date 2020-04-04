import os
import shutil
import glob
import time

import geopandas as gpd
import earthpy.clip as ec

import logging

import geo_util

TEST_CLIP_EXTENT = r"/Users/thozub/ShapeFileClipper/test_extent.shp"
TEST_SHAPE_FILE_DIRECTORY = r"/Users/thozub/ShapeFileClipper/test_shape_files"
TEST_SHAPE_FILES = glob.glob(os.path.join(TEST_SHAPE_FILE_DIRECTORY, "*.shp"))
TEST_OUTPUT_PATH = r"/Users/thozub/ShapeFileClipper/test_output"


def init_logging():
    """ Initialize logging. """

    log_format = "%(asctime)s  %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)


class ExecutionTimer:
    """ Timer class to stop execution time. """

    def __init__(self):
        self.start_time = None
        self.reset()

    def get_running_time(self):
        """ Returns the running time since creating this timer or since its last reset. """

        return time.time() - self.start_time

    def reset(self):
        """ Resets the timer. """

        self.start_time = time.time()

    def log_running_time(self):
        """ Logs the execution time since creating this timer or since its last reset. """

        logging.info("Execution time: {0:.0f} seconds".format(self.get_running_time()))


class ShapeFileClipperLogEntry:
    """ Log Entry class of ShapeFileClipper. """

    def __init__(self, result_message, ignored_values, execution_time, do_log_message_immediately=True):
        self.result_message = result_message
        self.ignored_values = ignored_values
        self.execution_time = execution_time

        if do_log_message_immediately:
            logging.info(result_message)

    def __repr__(self):
        if self.ignored_values is None or len(self.ignored_values) == 0:
            return "{}\nExecution Time: {}".format(self.result_message, self.execution_time)

        return "{}\nIgnored (invalid) Values:\n{}\nExecution Time: {}".format(
            self.result_message, self.ignored_values, self.execution_time)


class ShapeFileClipper:
    """ Shape File Clipper script. """

    def __init__(self, clip_shape_file, output_path, output_file_postfix):
        self.clip_extent = gpd.read_file(clip_shape_file)
        self.projected_clip_extents = {}  # applying flyweight pattern
        self.output_path = output_path
        self.output_file_postfix = output_file_postfix
        self.log = []

    def __generate_clipped_output_file_path(self, file_path):
        """ Generates the output file path based on the input shape file, output path
            and output file post fix. """

        name, extension = os.path.splitext(os.path.basename(file_path))
        new_file_name = "".join([name, self.output_file_postfix, extension])
        if self.output_path is None:
            return os.path.join(os.path.dirname(file_path), new_file_name)
        return os.path.join(self.output_path, new_file_name)

    def __clip_data_frame(self, data_frame):
        """ Clips given data frame. """

        clip_extent = self.clip_extent

        if clip_extent.crs != data_frame.crs:
            key = str(data_frame.crs)
            if key in self.projected_clip_extents:
                clip_extent = self.projected_clip_extents[key]
            else:
                clip_extent = clip_extent.to_crs(data_frame.crs)
                self.projected_clip_extents[key] = clip_extent

        # requires earthpy version 0.8.0 !
        clipped_data_frame = ec.clip_shp(data_frame, clip_extent)
        clipped_data_frame.crs = data_frame.crs
        return clipped_data_frame[~clipped_data_frame.is_empty]

    def __clip_shape_file(self, shape_file, fix_invalid_polygons=True):
        """ Clips given shape file. Fixes invalid polygon when parameter is
            set to True (default). """

        # load shape file
        data_frame = gpd.read_file(shape_file)

        shape_file_name = os.path.basename(shape_file)

        # fix invalid polygons
        if fix_invalid_polygons and geo_util.is_polygon_feature_set(data_frame):
            data_frame = geo_util.fix_polygons(data_frame)

        # check geometries and enrich with column is_valid
        valid_values, non_valid_values = geo_util.check_geometries(data_frame)

        clipped_data_frame = None
        if any(valid_values.intersects(self.clip_extent.unary_union)):
            clipped_data_frame = self.__clip_data_frame(valid_values)

        if clipped_data_frame is None or len(clipped_data_frame) == 0:
            return None, non_valid_values, "No features in {} within clipping extent. Ignored.".format(shape_file_name)

        return clipped_data_frame, non_valid_values, "{} successfully clipped.".format(shape_file_name)

    def __save_shape_file(self, data_frame, input_shape_file):
        """ Saves given data_frame to a shape file. Requires path to input_shape_file to generate
            output file path. Calls __generate_clipped_output_file_path(input_shape_file)
            internally. """

        output_file_path = self.__generate_clipped_output_file_path(input_shape_file)
        data_frame.to_file(driver="ESRI Shapefile", filename=output_file_path, encoding="UTF-8")
        return output_file_path

    def clip(self, shape_file):
        """ Clips given shape file. """

        logging.info("Processing {}...".format(os.path.basename(shape_file)))
        timer = ExecutionTimer()

        clipped_data_frame, ignored_values, result_message = self.__clip_shape_file(shape_file)

        self.log.append(ShapeFileClipperLogEntry(result_message, ignored_values, timer.get_running_time()))
        timer.reset()

        if clipped_data_frame is not None:
            output_file_path = self.__save_shape_file(clipped_data_frame, shape_file)

            result_message = "{} saved.".format(output_file_path)
            self.log.append(ShapeFileClipperLogEntry(result_message, None, timer.get_running_time()))

    def clip_and_project(self, shape_file, epsg_code):
        """ Clips given shape file and project result with given EPSG code. """

        logging.info("Processing {}...".format(os.path.basename(shape_file)))
        timer = ExecutionTimer()

        clipped_data_frame, ignored_values, result_message = self.__clip_shape_file(shape_file)

        self.log.append(ShapeFileClipperLogEntry(result_message, ignored_values, timer.get_running_time()))
        timer.reset()

        if clipped_data_frame is not None:
            clipped_data_frame = geo_util.project_data_frame(clipped_data_frame, epsg_code)
            output_file_path = self.__save_shape_file(clipped_data_frame, shape_file)

            result_message = "{} projected and saved.".format(os.path.basename(output_file_path))
            self.log.append(ShapeFileClipperLogEntry(result_message, None, timer.get_running_time()))

    def print_log(self):
        """ Prints log to console. """

        for log_entry in self.log:
            print(log_entry)


def clip_and_project(shape_files, clip_shape_file, output_path, output_file_postfix, epsg_code):
    """ Clip and project given shape files. """
    clipper = ShapeFileClipper(clip_shape_file, output_path, output_file_postfix)
    for shape_file in shape_files:
        clipper.clip_and_project(shape_file, epsg_code)
    # clipper.print_log()


def run_test():
    """ Runs test with given test data. """

    # clear output directory
    shutil.rmtree(TEST_OUTPUT_PATH, ignore_errors=True)
    os.mkdir(TEST_OUTPUT_PATH)

    init_logging()
    timer = ExecutionTimer()
    clip_and_project(TEST_SHAPE_FILES, TEST_CLIP_EXTENT, TEST_OUTPUT_PATH, "_clipped", 2961)
    timer.log_running_time()


if __name__ == '__main__':
    run_test()
