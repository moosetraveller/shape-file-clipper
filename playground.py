# from shapely.geometry import Point, LineString
#
# start_point = Point(0, 0)
# end_point = Point(100, 200)
#
# line = LineString([start_point, end_point])
#
# print("Line length: " + str(line.length))
# print("Line bounds: " + str(line.bounds))
#
# point = Point(50, 50)
# buffer = point.buffer(1.5)
#
# print("Buffer area: " + str(buffer.area))

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point
from pyproj import CRS

crs = CRS.from_epsg(4326).to_wkt()

# test/posts.csv -> lat,lon,timestamp,userid
csv = pd.read_csv("test/posts.csv", sep=",")
geometry = [Point(xy) for xy in zip(csv["lon"], csv["lat"])]

data = gpd.GeoDataFrame(csv, geometry=geometry, crs=crs)
data = data[data["userid"] == 61381975]

print(data.head())

data.to_file(driver="ESRI Shapefile", filename="test/posts.shp", encoding="UTF-8")



