""" 该模块是程序的主入口，负责控制整体流程，调用各个模块完成多段线的加载、合并、分割、法线生成、封闭形状构建等任务。 """

import os
from geometry.polyline import Polyline
from geometry.close_shape import ClosedShape
from geometry.normals import generate_infinite_normals_on_linestring_with_polyline, remove_crossing_normals
from file_io.file_io import (
    load_polylines_from_shp,
    save_north_south_lines_to_json,
    load_north_south_lines_from_json,
    save_split_points_to_file,
    load_split_points_from_file,
    save_closed_shapes_to_file,
    load_closed_shapes_from_file,
    load_merged_polyline_from_json,
    save_merged_polyline_to_json
)
from processing.merging import merge_polylines
from processing.splitting import split_polyline_by_points
from utils.helpers import find_point_in_closed_shapes

from shapely.geometry import LineString, Point

from visualization.plot import plot_polyline

def check_file_exists(file_path):
    return os.path.exists(file_path)

def main():
    os.makedirs("output", exist_ok=True)

    # 1. 加载中心线和边界线数据
    print("1. 加载多段线数据...")
    centerlines = load_polylines_from_shp("data/中心线平滑.shp")
    boundaries = load_polylines_from_shp("data/南北线_修改后.shp")

    # 2. 合并多段线
    merged_polyline_path = "output/merged_polyline.json"
    if check_file_exists(merged_polyline_path):
        print("2. 合并多段线... 已检测到缓存文件，跳过合并步骤。")
        merged_polyline = load_merged_polyline_from_json(merged_polyline_path)
        # plot_polyline(merged_polyline, title="Merged Polyline Visualization")
    else:
        print("2. 合并多段线... 开始计算。")
        merged_polyline = merge_polylines(centerlines, log=False)
        save_merged_polyline_to_json(merged_polyline, merged_polyline_path)
        # plot_polyline(merged_polyline, title="Merged Polyline Visualization")

    # 3. 分割南北线
    split_lines_path = "output/north_south_lines.json"
    if check_file_exists(split_lines_path):
        print("3. 分割多段线... 已检测到缓存文件，跳过分割步骤。")
        north_line, south_line = load_north_south_lines_from_json(split_lines_path)
    else:
        print("3. 分割多段线... 开始计算。")
        work_polyline=boundaries[0].line
        coords = list(work_polyline.coords)
        min_x_point = min(coords, key=lambda p: p[0])
        min_y_point = min(coords, key=lambda p: p[1])
        split_point1 = Point(min_x_point)
        split_point2 = Point(min_y_point)
        min_x_index = coords.index(split_point1.coords[0])
        min_y_index = coords.index(split_point2.coords[0])
        north_line, south_line = split_polyline_by_points(
            LineString(work_polyline),
            split_point1,
            split_point2,
            min_x_index,
            min_y_index,
            log=True
        )
        save_north_south_lines_to_json(north_line, south_line, split_lines_path)

    # 4. 生成法线
    normals_path = "output/normals.yaml"
    if check_file_exists(normals_path):
        print("4. 生成法线... 已检测到缓存文件，跳过法线生成步骤。")
        normals = load_split_points_from_file(normals_path)
    else:
        print("4. 生成法线... 开始计算。")
        normals = generate_infinite_normals_on_linestring_with_polyline(
            merged_polyline.line,
            north_line,
            south_line,
            interval=700
        )
        normals = remove_crossing_normals(normals)
        save_split_points_to_file(normals, normals_path)

    # 5. 封闭形状生成
    closed_shapes_path = "output/closed_shapes.yaml"
    if check_file_exists(closed_shapes_path):
        print("5. 封闭形状生成... 已检测到缓存文件，跳过封闭形状生成步骤。")
        closed_shapes = load_closed_shapes_from_file(closed_shapes_path)
    else:
        print("5. 封闭形状生成... 开始计算。")
        closed_shapes = []
        for i in range(len(normals) - 1):
            intersections = [normals[i][0], normals[i + 1][0]]
            work_line_1 = normals[i][1]
            work_line_2 = normals[i + 1][1]
            tangent_line_1 = LineString([intersections[0], intersections[1]])
            tangent_line_2 = LineString([intersections[1], intersections[0]])
            polygon = LineString([
                intersections[0],
                intersections[1],
                work_line_2.coords[-1],
                work_line_1.coords[-1],
                intersections[0]
            ])
            closed_shapes.append(
                ClosedShape(
                    intersections, work_line_1, work_line_2, tangent_line_1, tangent_line_2, polygon
                )
            )
        save_closed_shapes_to_file(closed_shapes, closed_shapes_path)

    # 6. 检查点是否在封闭形状内部
    print("6. 点在封闭形状内的检查...")
    test_point = Point(100, 200)
    containing_shape = find_point_in_closed_shapes(test_point, closed_shapes)
    if containing_shape:
        print("点位于封闭形状内。")
    else:
        print("点不在任何封闭形状内。")

    print("所有步骤完成，结果已保存至 output 文件夹。")

if __name__ == "__main__":
    main()