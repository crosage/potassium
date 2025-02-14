""" 该模块是程序的主入口，负责控制整体流程，调用各个模块完成多段线的加载、合并、分割、法线生成、封闭形状构建等任务。 """

import os
from processing.close_shape import generate_closed_shapes_with_polylines
from processing.normals import generate_infinite_normals_on_linestring_with_polyline
from file_io.file_io import (
    load_polylines_from_shp,
)
from processing.ditch import process_ditch_endpoints
from processing.merging import merge_polylines
from processing.splitting import split_polyline_by_points
from shapely.geometry import LineString, Point

def check_file_exists(file_path):
    return os.path.exists(file_path)

def work(meters):
    os.makedirs("output", exist_ok=True)
    print("1. 加载多段线数据...")
    centerlines = load_polylines_from_shp(f"data/arc_smooth/PEAK_{meters}.shp")
    boundaries = load_polylines_from_shp("data/南北线_修改后.shp")

    # 2. 合并多段线
    print("2. 合并多段线... 开始计算。")
    merged_polyline = merge_polylines(centerlines, log=False)

    # 3. 分割南北线
    print("3. 分割多段线... 开始计算。")
    work_polyline = boundaries[0].line
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
    )

    # 4. 生成法线
    print("4. 生成法线... 开始计算。")
    normals = generate_infinite_normals_on_linestring_with_polyline(
        merged_polyline.line,
        north_line,
        south_line,
        interval=1000
    )

    # 5. 封闭形状生成
    print("5. 封闭形状生成... 开始计算。")
    closed_shapes = generate_closed_shapes_with_polylines(normals, north_line, south_line, log=False)

    # 6. 检查点是否在封闭形状内部
    ditch_file = "data\\20230305清沟_hz.shp"
    ditchs = load_polylines_from_shp(ditch_file, False)
    process_ditch_endpoints(ditchs, closed_shapes, merged_polyline, f"output\ditch{meters}", True)


def main():
    work(1000)
    work(5000)
    work(6000)
    work(7000)
    work(10000)
    work(12000)

if __name__ == "__main__":
    main()
