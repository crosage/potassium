import geopandas as gpd
from tqdm import tqdm
from geometry.close_shape import ClosedShape
from geometry.polyline import Polyline
from shapely.geometry import LineString, Point, MultiLineString, Polygon
import json
from file_io.config import load_config, update_path


# ========================
# 从配置中获取路径
# ========================

config = load_config()

def get_default_path(key):
    """
    从配置中获取默认路径。
    """
    return config.get(key, "")


# ========================
# 北岸与南岸线相关操作
# ========================

def save_left_right_lines_to_json(left_line, right_line, filename=None):
    """
    将北岸和南岸线保存为 JSON 文件。
    """
    filename = filename or get_default_path("left_right_lines")
    data = {
        'left_line': list(left_line.coords),
        'right_line': list(right_line.coords)
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Lines saved to {filename}")


def load_left_right_lines_from_json(filename=None):
    """
    从 JSON 文件中加载北岸和南岸线。
    """
    filename = filename or get_default_path("left_right_lines")
    with open(filename, 'r') as f:
        data = json.load(f)

    left_line = LineString(data['left_line'])
    right_line = LineString(data['right_line'])
    return left_line, right_line


# ========================
# 分割点相关操作
# ========================

def save_split_points_to_file(split_points, file_path=None):
    """
    保存分割点和法线数据。
    """
    file_path = file_path or get_default_path("split_points")
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
        json.dump(serialized_results, f, indent=4)
    print(f"Split points saved to {file_path}")


def load_split_points_from_file(file_path=None):
    """
    从文件中加载分割点和法线数据。
    """
    file_path = file_path or get_default_path("split_points")
    with open(file_path, "r") as f:
        data = json.load(f)

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

def save_closed_shapes_to_file(closed_shapes, file_path=None):
    """
    保存封闭形状数据。
    """
    serialized_shapes = []

    for i, shape in tqdm(enumerate(closed_shapes), total=len(closed_shapes), desc="处理清沟", unit="个"):
        try:
            serialized_shape = {
                "intersections": [
                    {"x": point[0], "y": point[1]} for point in shape.intersections
                ],
                "work_line_1": [
                    {"x": coord[0], "y": coord[1]} for coord in shape.work_line_1.coords
                ],
                "work_line_2": [
                    {"x": coord[0], "y": coord[1]} for coord in shape.work_line_2.coords
                ],
                "tangent_line_1": [
                    {"x": coord[0], "y": coord[1]} for coord in shape.tangent_line_1.coords
                ],
                "tangent_line_2": [
                    {"x": coord[0], "y": coord[1]} for coord in shape.tangent_line_2.coords
                ],
                "polygon": [
                    {"x": coord[0], "y": coord[1]} for coord in shape.polygon.exterior.coords
                ],
            }
            serialized_shapes.append(serialized_shape)
        except Exception as e:
            print(f"Error serializing ClosedShape at index {i}: {e}")
            continue  # 跳过当前 ClosedShape，继续处理下一个

    # 保存结果到文件
    try:
        with open(file_path, "w") as f:
            json.dump(serialized_shapes, f, indent=4)
        print(f"Closed Shapes saved successfully to {file_path}")
    except Exception as e:
        print(f"Error saving Closed Shapes to file: {e}")


def load_closed_shapes_from_file(file_path=None):
    """
    加载封闭形状数据。
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    closed_shapes = []
    for item in data:
        intersections = [Point(p["x"], p["y"]) for p in item["intersections"]]
        work_line_1 = LineString([(coord["x"], coord["y"]) for coord in item["work_line_1"]])
        work_line_2 = LineString([(coord["x"], coord["y"]) for coord in item["work_line_2"]])
        tangent_line_1 = LineString([(coord["x"], coord["y"]) for coord in item["tangent_line_1"]])
        tangent_line_2 = LineString([(coord["x"], coord["y"]) for coord in item["tangent_line_2"]])
        polygon = Polygon([(coord["x"], coord["y"]) for coord in item["polygon"]])

        closed_shape = ClosedShape(
            intersections=intersections,
            work_line_1=work_line_1,
            work_line_2=work_line_2,
            tangent_line_1=tangent_line_1,
            tangent_line_2=tangent_line_2,
            polygon=polygon,
        )
        closed_shapes.append(closed_shape)

    return closed_shapes


# ========================
# 合并后的多段线操作
# ========================

def save_merged_polyline_to_json(polyline, filename=None):
    """
    将合并后的多段线保存为 JSON 文件。
    """
    filename = filename or get_default_path("merged_polyline")
    data = {
        'id': polyline.id,
        'points': [{'x': point.x, 'y': point.y} for point in polyline.points]
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Merged polyline saved to {filename}")


def load_merged_polyline_from_json(filename=None):
    """
    从 JSON 文件中加载合并后的多段线。
    """
    filename = filename or get_default_path("merged_polyline")
    with open(filename, 'r') as f:
        data = json.load(f)

    id = data['id']
    points = [Point(coord['x'], coord['y']) for coord in data['points']]
    return Polyline(id=id, points=points)


def load_polylines_from_shp(file_path, ignore=False,charset="UTF-8"):
    """
    从 shapefile 加载多段线，转换坐标系，并包含其所有的属性。
    """
    try:
        gdf = gpd.read_file(file_path, encoding=charset)
    except Exception as e:
        print(f"读取 shapefile 时出错: {e}")
        return []

    print("原始 CRS:", gdf.crs)
    #转化为米坐标系方便运算
    gdf = gdf.to_crs("EPSG:32649")
    print("转换后的 CRS:", gdf.crs)

    polylines = []
    for index, row in gdf.iterrows():
        if index == 8 and ignore:
            continue
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        attributes = row.to_dict()
        attributes.pop('geometry')
        def process_geom(line_geom, poly_id):
            points = [Point(coord) for coord in line_geom.coords]
            polyline_id = attributes.get('CODE', poly_id)
            polyline = Polyline(id=polyline_id, points=points)
            polyline.attributes = attributes
            polylines.append(polyline)

        if isinstance(geom, LineString):
            process_geom(geom, index)
        elif isinstance(geom, MultiLineString):
            for i, part in enumerate(geom.geoms):
                process_geom(part, f"{index}_{i}")

    return polylines
