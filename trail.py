import os
import csv
import pandas as pd
import geopandas as gpd

from shapely import geometry
from pyproj import CRS

crs = CRS.from_epsg(4326).to_wkt()
projected_crs = CRS.from_epsg(2961).to_wkt()

output_fp = r"data/digby.shp"

columns = ["id", "name", "subname", "type", "address"]
data_frame = gpd.GeoDataFrame(pd.DataFrame(columns=columns), geometry=[], crs=crs)

with open(r"data/trails.csv", "r") as file:
    csv_reader = csv.reader(file, delimiter=",")
    next(csv_reader, None)  # skip the headers
    for index, row in enumerate(csv_reader):
        point = geometry.Point(float(row[5]), float(row[4]))
        data_frame.loc[index] = [row[0], row[1], row[2], row[3], row[7], point]

data_frame.to_crs(projected_crs)
data_frame.to_file(driver="ESRI Shapefile", filename=output_fp, encoding="UTF-8")