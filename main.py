""" 该模块是程序的主入口，负责控制整体流程，调用各个模块完成多段线的加载、合并、分割、法线生成、封闭形状构建等任务。 """

import os
from processing.close_shape import generate_closed_shapes_with_polylines
from processing.normals import generate_infinite_normals_on_linestring_with_polyline
from file_io.file_io import (
    load_polylines_from_shp, load_north_south_lines_from_json, save_north_south_lines_to_json,
    load_merged_polyline_from_json, save_merged_polyline_to_json, load_split_points_from_file,
    save_split_points_to_file, load_closed_shapes_from_file, save_closed_shapes_to_file,
)
from processing.ditch import process_ditch_endpoints
from processing.merging import merge_polylines
from processing.splitting import split_polyline_by_points
from shapely.geometry import LineString, Point

from visualization.plot import plot_normals, plot_closed_shapes, plot_polyline


def check_file_exists(file_path):
    return os.path.exists(file_path)

def smooth_work(meters):
    os.makedirs("output", exist_ok=True)

    # 1. 加载中心线和边界线数据
    print("1. 加载多段线数据...")
    centerlines = load_polylines_from_shp(f"data/arc_smooth/PEAK_{meters}.shp")

    boundaries = load_polylines_from_shp("data/南北线_修改后.shp")

    # 2. 合并多段线
    merged_polyline_path = f"output/merged_polyline_PEAK{meters}.json"
    if check_file_exists(merged_polyline_path):
        print("2. 合并多段线... 已检测到缓存文件，跳过合并步骤。")
        merged_polyline = load_merged_polyline_from_json(merged_polyline_path)
        # plot_polyline(merged_polyline, title="Merged Polyline Visualization")
    else:
        print("2. 合并多段线... 开始计算。")
        merged_polyline = merge_polylines(centerlines, log=False)
        save_merged_polyline_to_json(merged_polyline, merged_polyline_path)
        plot_polyline(merged_polyline, title="Merged Polyline Visualization")

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
    normals_path = f"output/normals_PEAK{meters}.json"
    if check_file_exists(normals_path):
        print("4. 生成法线... 已检测到缓存文件，跳过法线生成步骤。")
        normals = load_split_points_from_file(normals_path)
        # plot_normals(normals, north_line, south_line, merged_polyline.line,x_min=-290000,x_max=-270000,y_min=4550000,y_max=4570000)

    else:
        print("4. 生成法线... 开始计算。")
        normals = generate_infinite_normals_on_linestring_with_polyline(
            merged_polyline.line,
            north_line,
            south_line,
            interval=100
        )
        save_split_points_to_file(normals, normals_path)

    # 5. 封闭形状生成
    closed_shapes_path = f"output/closed_shapes_PEAK{meters}_split.json"
    if check_file_exists(closed_shapes_path):
        print("5. 封闭形状生成... 已检测到缓存文件，跳过封闭形状生成步骤。")
        closed_shapes = load_closed_shapes_from_file(closed_shapes_path)
        # plot_closed_shapes(closed_shapes, north_line, south_line, merged_polyline.line,x_min=-290000,x_max=-270000,y_min=4550000,y_max=4570000)

    else:
        print("5. 封闭形状生成... 开始计算。")
        closed_shapes = generate_closed_shapes_with_polylines(normals, north_line, south_line,500, log=False)
        save_closed_shapes_to_file(closed_shapes, closed_shapes_path)

    # 6. 检查点是否在封闭形状内部
    ditch_file="data\\清沟汇总_2024-2025年度20250122.shp"
    ditchs = load_polylines_from_shp(ditch_file, False)
    process_ditch_endpoints(ditchs,closed_shapes,north_line,south_line,merged_polyline,f"output\ditch_PEAK{meters}",True)

def origin_work(name):
    os.makedirs("output", exist_ok=True)

    # 1. 加载中心线和边界线数据
    print("1. 加载多段线数据...")
    import geopandas as gpd
    gdf = gpd.read_file(f"data/{name}").to_crs("EPSG:32650")
    print(gdf.length.sum())
    return
    centerlines = load_polylines_from_shp(f"data/{name}")

    boundaries = load_polylines_from_shp("data/南北线_修改后.shp")

    # 2. 合并多段线
    merged_polyline_path = f"output/merged_polyline_origin.json"
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
    normals_path = f"output/normals_origin.json"
    if check_file_exists(normals_path):
        print("4. 生成法线... 已检测到缓存文件，跳过法线生成步骤。")
        normals = load_split_points_from_file(normals_path)
        plot_normals(normals, north_line, south_line, merged_polyline.line,x_min=-520000,x_max=-500000,y_min=4200000,y_max=4220000)

    else:
        print("4. 生成法线... 开始计算。")
        normals = generate_infinite_normals_on_linestring_with_polyline(
            merged_polyline.line,
            north_line,
            south_line,
            interval=100
        )
        save_split_points_to_file(normals, normals_path)

    # 5. 封闭形状生成
    closed_shapes_path = f"output/closed_shapes_origin_split.json"
    if check_file_exists(closed_shapes_path):
        print("5. 封闭形状生成... 已检测到缓存文件，跳过封闭形状生成步骤。")
        closed_shapes = load_closed_shapes_from_file(closed_shapes_path)
        plot_closed_shapes(closed_shapes, north_line, south_line, merged_polyline.line,x_min=-520000,x_max=-500000,y_min=4200000,y_max=4220000)

    else:
        print("5. 封闭形状生成... 开始计算。")
        closed_shapes = generate_closed_shapes_with_polylines(normals, north_line, south_line,500, log=True)
        save_closed_shapes_to_file(closed_shapes, closed_shapes_path)

    # 6. 检查点是否在封闭形状内部
    ditch_file="data\\清沟汇总_2024-2025年度20250122.shp"
    ditchs = load_polylines_from_shp(ditch_file, False)
    process_ditch_endpoints(ditchs,closed_shapes,north_line,south_line,merged_polyline,f"output\ditch_origin",True)

def main():
    # origin_work("中心线平滑.shp")
    # smooth_work("SM2_1000")
    smooth_work("SM2_5000")
    # smooth_work("SM2_6000")
    # smooth_work("SM2_10000")

if __name__ == "__main__":
    main()
