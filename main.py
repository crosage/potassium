"""
该模块是程序的主入口，负责控制整体流程，调用各个模块完成多段线的加载、合并、分割、法线生成、封闭形状构建等任务。
通过重构，将重复的逻辑抽象为单一的流水线函数，使用配置来管理不同的任务。
"""
import os
import geopandas as gpd
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
    """检查文件是否存在"""
    return os.path.exists(file_path)

def run_processing_pipeline(config):
    """
    运行完整的地理数据处理流水线。

    Args:
        config (dict): 包含所有必需路径和参数的配置字典。
            - job_name (str): 任务名称，用于生成输出文件名。
            - centerline_path (str): 中心线shapefile的路径。
            - boundary_path (str): 边界线shapefile的路径。
            - ditch_path (str): 沟渠shapefile的路径。
            - output_dir (str): 输出目录。
            - normal_interval (int): 生成法线的间隔。
            - shape_max_length (int): 封闭形状的最大长度。
            - plot_config (dict, optional): 可视化绘图的配置。
    """
    job_name = config["job_name"]
    output_dir = config["output_dir"]
    plot_cfg = config.get("plot_config") # 使用 .get 避免 KeyErorr

    print(f"\n--- 开始处理任务: {job_name} ---")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 路径定义
    merged_polyline_path = os.path.join(output_dir, f"merged_polyline_{job_name}.json")
    split_lines_path = os.path.join(output_dir, "north_south_lines.json") # 边界分割通常是固定的，可以共享
    normals_path = os.path.join(output_dir, f"normals_{job_name}.json")
    closed_shapes_path = os.path.join(output_dir, f"closed_shapes_{job_name}.json")
    ditch_output_path_prefix = os.path.join(output_dir, f"ditch_{job_name}")

    # 1. 加载中心线和边界线数据
    print("1. 加载多段线数据...")
    centerlines = load_polylines_from_shp(config["centerline_path"])
    boundaries = load_polylines_from_shp(config["boundary_path"])

    # 2. 合并多段线
    if check_file_exists(merged_polyline_path):
        print(f"2. 合并多段线... 检测到缓存文件，跳过。({merged_polyline_path})")
        merged_polyline = load_merged_polyline_from_json(merged_polyline_path)
    else:
        print("2. 合并多段线... 开始计算。")
        merged_polyline = merge_polylines(centerlines, log=False)
        save_merged_polyline_to_json(merged_polyline, merged_polyline_path)
        if plot_cfg:
            plot_polyline(merged_polyline, title=f"Merged Polyline - {job_name}")

    # 3. 分割南北线 (如果文件不存在则计算)
    if check_file_exists(split_lines_path):
        print(f"3. 分割多段线... 检测到缓存文件，跳过。({split_lines_path})")
        north_line, south_line = load_north_south_lines_from_json(split_lines_path)
    else:
        print("3. 分割多段线... 开始计算。")
        work_polyline = boundaries[0].line
        coords = list(work_polyline.coords)
        # 基于业务逻辑寻找分割点
        min_x_point = min(coords, key=lambda p: p[0])
        min_y_point = min(coords, key=lambda p: p[1])
        split_point1 = Point(min_x_point)
        split_point2 = Point(min_y_point)
        min_x_index = coords.index(split_point1.coords[0])
        min_y_index = coords.index(split_point2.coords[0])
        north_line, south_line = split_polyline_by_points(
            LineString(work_polyline), split_point1, split_point2, min_x_index, min_y_index, log=True
        )
        save_north_south_lines_to_json(north_line, south_line, split_lines_path)

    # 4. 生成法线
    if check_file_exists(normals_path):
        print(f"4. 生成法线... 检测到缓存文件，跳过。({normals_path})")
        normals = load_split_points_from_file(normals_path)
    else:
        print("4. 生成法线... 开始计算。")
        normals = generate_infinite_normals_on_linestring_with_polyline(
            merged_polyline.line, north_line, south_line, interval=config["normal_interval"]
        )
        save_split_points_to_file(normals, normals_path)

    if plot_cfg and "normals" in plot_cfg:
        plot_normals(normals, north_line, south_line, merged_polyline.line, **plot_cfg["normals"])

    # 5. 封闭形状生成
    if check_file_exists(closed_shapes_path):
        print(f"5. 封闭形状生成... 检测到缓存文件，跳过。({closed_shapes_path})")
        closed_shapes = load_closed_shapes_from_file(closed_shapes_path)
    else:
        print("5. 封闭形状生成... 开始计算。")
        closed_shapes = generate_closed_shapes_with_polylines(
            normals, north_line, south_line, max_length=config["shape_max_length"], log=False
        )
        save_closed_shapes_to_file(closed_shapes, closed_shapes_path)

    if plot_cfg and "closed_shapes" in plot_cfg:
        plot_closed_shapes(closed_shapes, north_line, south_line, merged_polyline.line, **plot_cfg["closed_shapes"])

    # 6. 检查点是否在封闭形状内部
    print("6. 处理沟渠数据...")
    ditchs = load_polylines_from_shp(config["ditch_path"], has_z=False)
    process_ditch_endpoints(
        ditchs, closed_shapes, north_line, south_line, merged_polyline, ditch_output_path_prefix, save_results=True
    )

    print(f"--- 任务: {job_name} 处理完成 ---")

def main():
    tasks = [
        {
            "job_name": "PEAK_SM2_5000",
            "centerline_path": "data/arc_smooth/PEAK_SM2_5000.shp",
            "boundary_path": "data/南北线_修改后.shp",
            "ditch_path": os.path.join("data", "清沟汇总_2024-2025年度20250122.shp"),
            "output_dir": "output",
            "normal_interval": 100,
            "shape_max_length": 500,
            "plot_config": {
                "normals": {"x_min": -290000, "x_max": -270000, "y_min": 4550000, "y_max": 4570000},
                "closed_shapes": {"x_min": -290000, "x_max": -270000, "y_min": 4550000, "y_max": 4570000},
            }
        },
    ]

    for task_config in tasks:
        run_processing_pipeline(task_config)

def calc_shp_length(shp_path, crs="EPSG:32650"):
    print(f"\n计算文件 '{shp_path}' 的总长度...")
    try:
        gdf = gpd.read_file(shp_path)
        if gdf.crs.to_string() != crs:
            print(f"转换坐标系到 {crs}...")
            gdf = gdf.to_crs(crs)
        total_length = gdf.length.sum()
        print(f"总长度: {total_length:.2f} 米")
        return total_length
    except Exception as e:
        print(f"计算长度时出错: {e}")
        return None

if __name__ == "__main__":
    main()