"""
该模块提供了多段线、法线、封闭形状等几何数据的文件读写功能。
"""

import geopandas as gpd
from geometry.polyline import Polyline
from shapely.geometry import LineString, Point, MultiLineString, Polygon
import yaml
import json


# ========================
# 多段线相关文件操作
# ========================

def load_polylines_from_shp(file_path, ignore=False):
    """
    从 Shapefile 文件中加载多段线数据。
    """
    gdf = gpd.read_file(file_path)
    print("原始 CRS:", gdf.crs)
    gdf = gdf.to_crs("EPSG:32650")
    print("转换后的 CRS:", gdf.crs)

    polylines = []
    for idx, geom in enumerate(gdf.geometry):
        if idx == 8 and ignore:
            continue
        if isinstance(geom, LineString):
            points = [Point(coord) for coord in geom.coords]
            polylines.append(Polyline(id=idx, points=points))
        elif isinstance(geom, MultiLineString):
            for sub_idx, line in enumerate(geom.geoms):
                points = [Point(coord) for coord in line.coords]
                polylines.append(Polyline(id=f"{idx}_{sub_idx}", points=points))
    return polylines


# ========================
# 北岸与南岸线相关操作
# ========================

def save_north_south_lines_to_json(north_line, south_line, filename):
    """
    将北岸和南岸线保存为 JSON 文件。
    """
    data = {
        'north_line': list(north_line.coords),
        'south_line': list(south_line.coords)
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Lines saved to {filename}")


def load_north_south_lines_from_json(filename):
    """
    从 JSON 文件中加载北岸和南岸线。
    """
    with open(filename, 'r') as f:
        data = json.load(f)

    north_line = LineString(data['north_line'])
    south_line = LineString(data['south_line'])
    return north_line, south_line


# ========================
# 分割点相关操作
# ========================

def save_split_points_to_file(split_points, file_path, file_format="yaml"):
    """
    保存分割点和法线数据。
    """
    if file_format not in ["yaml", "json"]:
        raise ValueError("file_format must be 'yaml' or 'json'")

    serialized_results = [
        {
            "point": {"x": point.x, "y": point.y},
            "normal_line": [
                {"x": coord[0], "y": coord[1]} for coord in normal_line.coords
            ]
        }
        for point, normal_line in split_points
    ]

    with open(file_path, "w") as f:
        if file_format == "yaml":
            yaml.dump(serialized_results, f, default_flow_style=False)
        else:
            json.dump(serialized_results, f, indent=4)
    print(f"Split points saved to {file_path}")


def load_split_points_from_file(file_path, is_yaml=True):
    """
    从文件中加载分割点和法线数据。
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f) if is_yaml else json.load(f)

    split_points = [
        (
            Point(item["point"]["x"], item["point"]["y"]),
            LineString([(coord["x"], coord["y"]) for coord in item["normal_line"]])
        )
        for item in data
    ]

    return split_points


# ========================
# 封闭形状相关操作
# ========================

def save_closed_shapes_to_file(closed_shapes, file_path, file_format="yaml"):
    """
    保存封闭形状数据。
    """
    if file_format not in ["yaml", "json"]:
        raise ValueError("file_format must be 'yaml' or 'json'")

    serialized_shapes = []
    for shape in closed_shapes:
        serialized_shapes.append({
            "intersections": [{"x": p[0], "y": p[1]} for p in shape.intersections],
            "polygon": [{"x": coord[0], "y": coord[1]} for coord in shape.polygon.exterior.coords]
        })

    with open(file_path, "w") as f:
        if file_format == "yaml":
            yaml.dump(serialized_shapes, f, default_flow_style=False)
        else:
            json.dump(serialized_shapes, f, indent=4)
    print(f"Closed shapes saved to {file_path}")


def load_closed_shapes_from_file(file_path, is_yaml=True):
    """
    加载封闭形状数据。
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f) if is_yaml else json.load(f)

    closed_shapes = []
    for item in data:
        intersections = [Point(p["x"], p["y"]) for p in item["intersections"]]
        polygon = Polygon([(coord["x"], coord["y"]) for coord in item["polygon"]])
        closed_shapes.append({"intersections": intersections, "polygon": polygon})

    return closed_shapes


# ========================
# 合并后的多段线操作
# ========================

def save_merged_polyline_to_json(polyline, filename):
    """
    将合并后的多段线保存为 JSON 文件。
    """
    data = {
        'id': polyline.id,
        'points': [{'x': point.x, 'y': point.y} for point in polyline.points]
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Merged polyline saved to {filename}")


def load_merged_polyline_from_json(filename):
    """
    从 JSON 文件中加载合并后的多段线。
    """
    with open(filename, 'r') as f:
        data = json.load(f)

    id = data['id']
    points = [Point(coord['x'], coord['y']) for coord in data['points']]
    return Polyline(id=id, points=points)

# ========================
# 平滑后的多段线操作
# ========================

def save_smoothed_polyline_to_json(polyline, filename):
    """
    将合并后的多段线保存为 JSON 文件。
    """
    data = {
        'id': polyline.id,
        'points': [{'x': point.x, 'y': point.y} for point in polyline.points]
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Merged polyline saved to {filename}")


def load_smoothed_polyline_from_json(filename):
    """
    从 JSON 文件中加载合并后的多段线。
    """
    with open(filename, 'r') as f:
        data = json.load(f)

    id = data['id']
    points = [Point(coord['x'], coord['y']) for coord in data['points']]
    return Polyline(id=id, points=points)