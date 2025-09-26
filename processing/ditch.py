import os
import csv
import hashlib

from pyproj import Geod, Transformer
from shapely import LineString, MultiLineString, Point
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import rcParams
import geopandas as gpd
import pandas as pd
from rtree import index  # 空间索引

from file_io.file_io import load_polylines_from_shp
from processing.splitting import extract_subcurve
from utils.helpers import make_shape_finder, extract_subcurve_in_polygon_with_debug_plot, extract_subcurve_in_polygon

# --- Matplotlib 全局设置 ---
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
rcParams['axes.unicode_minus'] = False
def _center_of_geom(geom):
    # 支持 LineString/Polygon/Point
    c = geom.centroid
    return float(c.x), float(c.y)

def _to_lonlat(x, y, src_crs="EPSG:32649", dst_crs="EPSG:4326"):
    tf = Transformer.from_crs(src_crs, dst_crs, always_xy=True).transform
    lon, lat = tf(x, y)
    return float(lon), float(lat)

def _square_view_bbox_in_degrees(center_geom_src, buffer_m=5000,
                                 source_crs="EPSG:32649", display_crs="EPSG:4326"):
    """
    返回在 display_crs(经纬度) 下的方形窗口(bounds): (min_lon, min_lat, max_lon, max_lat)。
    在中心点处用大地线前进 buffer_m 到东/西/北/南，选更大的角度半径，保证方形且至少覆盖 ~buffer_m。
    """
    # 1) 取中心点（源坐标）
    cx, cy = _center_of_geom(center_geom_src)

    # 2) 转到经纬度
    lon0, lat0 = _to_lonlat(cx, cy, source_crs, display_crs)

    # 3) 选择椭球：4326≈WGS84；4490≈GRS80
    if display_crs == "EPSG:4490":
        geod = Geod(ellps="GRS80")
    else:
        geod = Geod(ellps="WGS84")

    # 4) 沿四个方位偏移 buffer_m，得到四个点
    lon_e, lat_e, _ = geod.fwd(lon0, lat0, 90,  buffer_m)   # 东
    lon_w, lat_w, _ = geod.fwd(lon0, lat0, 270, buffer_m)   # 西
    lon_n, lat_n, _ = geod.fwd(lon0, lat0, 0,   buffer_m)   # 北
    lon_s, lat_s, _ = geod.fwd(lon0, lat0, 180, buffer_m)   # 南

    # 5) 经/纬方向的半幅（度）
    half_lon = max(abs(lon_e - lon0), abs(lon0 - lon_w))
    half_lat = max(abs(lat_n - lat0), abs(lat0 - lat_s))

    # 6) 取更大的那个，作为正方形半径（度）
    half_deg = max(half_lon, half_lat)

    return lon0 - half_deg, lat0 - half_deg, lon0 + half_deg, lat0 + half_deg


def process_ditch_endpoints(ditchs, closed_shapes, left_line, right_line, dam_line, centerline,
                            save_path=None, log=True, manual_shp_path=None):
    """
    高效处理清沟：只投影到堤坝线，同时绘制南北岸线和中心线作为背景。
    """
    all_geometries_for_shp = []

    if not save_path:
        log = False

    # 加载人工投影数据 (逻辑不变)
    manual_projections = {}
    if manual_shp_path and os.path.exists(manual_shp_path):
        print(f"--- 正在使用自定义函数加载人工投影数据: {manual_shp_path} ---")
        manual_polylines = load_polylines_from_shp(manual_shp_path,ignore=False)
        if not manual_polylines:
            print("⚠️ 未能从人工投影文件加载任何数据。")
            manual_shp_path = None
        else:
            for polyline in manual_polylines:
                attrs = polyline.attributes
                river_part = attrs.get('RIVERPART')
                code = attrs.get('CODE')
                if river_part is not None and code is not None:
                    composite_key = (river_part, code)
                    new_line = LineString(polyline.points)
                    if composite_key in manual_projections:
                        existing_geom = manual_projections[composite_key]
                        if isinstance(existing_geom, LineString):
                            manual_projections[composite_key] = MultiLineString([existing_geom, new_line])
                        elif isinstance(existing_geom, MultiLineString):
                            manual_projections[composite_key] = MultiLineString(list(existing_geom.geoms) + [new_line])
                    else:
                        manual_projections[composite_key] = new_line
            if not manual_projections:
                print("⚠️ 错误: 人工投影数据中缺少 'RIVERPART' 和/或 'CODE' 字段，无法进行匹配。")
                manual_shp_path = None
            else:
                print(f"✅ 成功加载并处理了 {len(manual_projections)} 条人工投影。")



    # --- 创建空间索引 (逻辑不变) ---
    if log:
        print("正在为背景区域创建空间索引...")
        idx_shapes = index.Index()
        for i, shape in enumerate(closed_shapes):
            idx_shapes.insert(i, shape.polygon.bounds)
        print("✅ 空间索引创建完成。")

    # --- CSV 文件 (更新) ---
    if save_path:
        os.makedirs(save_path, exist_ok=True)
        csv_filename = os.path.join(save_path, "ditch_results.csv")
    else:
        csv_filename = "ditch_results.csv"

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # 更新CSV表头，移除中心线投影
        csv_writer.writerow([
            "name", "DATE", "RIVERPART", "CODE",
            "清沟实际长度", "堤坝线投影长度", "人工投影长度"
        ])
        finder = make_shape_finder(closed_shapes)

        for ditch in tqdm(ditchs, desc="处理所有清沟", unit="条"):
            start_point, end_point = ditch.points[0], ditch.points[-1]

            # --- 起点处理 (MODIFIED) ---
            # 直接使用 finder 返回的 shape 对象中预设的切线进行投影
            find_result_start = finder(start_point)
            if find_result_start is None:
                print(f"⚠️ 警告: 未能为清沟 '{ditch_attributes.get('CODE', ditch.id)}' 的起点找到封闭区域。")

                if log and save_path:
                    debug_save_path = os.path.join(save_path, f"DEBUG_ditch_{ditch.id}_START_POINT_OUTSIDE.png")
                    # --- 调用修改后的函数，并传入 ditch.line ---
                    plot_debug_point_outside_shapes(
                        point_to_check=start_point,
                        all_closed_shapes=closed_shapes,
                        ditch_line=ditch.line,  # <--- 新增传递此参数
                        ditch_info=str(ditch.id),
                        point_type="起点",
                        save_path=debug_save_path
                    )
                continue
            start_index, start_shape = find_result_start
            proj_start_dam_point = start_shape.tangent_line_1.interpolate(
                start_shape.tangent_line_1.project(start_point)
            ) if start_shape and hasattr(start_shape, 'tangent_line_1') else None

            # --- 终点处理 (MODIFIED) ---
            # 同样，直接使用 finder 返回的 shape 对象进行投影
            find_result_end = finder(end_point)
            if find_result_end is None:
                print(f"⚠️ 警告: 未能为清沟 '{ditch_attributes.get('CODE', ditch.id)}' 的终点找到封闭区域。")

                if log and save_path:
                    debug_save_path = os.path.join(save_path, f"DEBUG_ditch_{ditch.id}_END_POINT_OUTSIDE.png")
                    # --- 调用修改后的函数，并传入 ditch.line ---
                    plot_debug_point_outside_shapes(
                        point_to_check=end_point,
                        all_closed_shapes=closed_shapes,
                        ditch_line=ditch.line,  # <--- 新增传递此参数
                        ditch_info=str(ditch.id),
                        point_type="终点",
                        save_path=debug_save_path
                    )
                continue
            end_index, end_shape = find_result_end
            proj_end_dam_point = end_shape.tangent_line_1.interpolate(
                end_shape.tangent_line_1.project(end_point)
            ) if end_shape and hasattr(end_shape, 'tangent_line_1') else None

            # --- 计算投影长度 ---
            # 注意：这里的长度计算仍然是在“完整”的堤坝线上进行的，这是正确的逻辑
            if proj_start_dam_point and proj_end_dam_point:
                dam_length = extract_subcurve(dam_line, proj_start_dam_point, proj_end_dam_point).length
            else:
                dam_length = 0

            ditch_length = ditch.line.length

            # 人工投影长度计算
            ditch_attributes = ditch.attributes
            river_part = ditch_attributes.get('RIVERPART')
            code = ditch_attributes.get('CODE')
            manual_geom = None
            if river_part is not None and code is not None:
                composite_key = (river_part, code)
                manual_geom = manual_projections.get(composite_key)
            manual_length = manual_geom.length if manual_geom else 0

            # --- CSV 保存 ---
            csv_writer.writerow([
                ditch_attributes.get('name', 'N/A'), ditch_attributes.get('DATE', 'N/A'),
                ditch_attributes.get('RIVERPART', 'N/A'), ditch_attributes.get('CODE', ditch.id),
                f"{ditch_length:.2f}", f"{dam_length:.2f}", f"{manual_length:.2f}"
            ])

            # --- SHP 记录 (更新) ---
            base_record = ditch_attributes.copy()
            base_record.update({
                'ditch_len': ditch_length,
                'dam_len': dam_length,
                'manual_len': manual_length
            })

            geometries_to_save = {
                'original_ditch': ditch.line,
                'dam_projection': extract_subcurve(dam_line, proj_start_dam_point,
                                                   proj_end_dam_point) if dam_length > 0 else None,
                'manual_projection': manual_geom
            }

            for line_type, geom in geometries_to_save.items():
                if geom and not geom.is_empty:
                    record = base_record.copy()
                    record['line_type'] = line_type
                    record['geometry'] = geom
                    all_geometries_for_shp.append(record)

            # --- 绘图 (更新) ---
            if log:
                safe_name = str(ditch_attributes.get('name', 'ditch')).replace('/', '-').replace('\\', '-')
                x_ditch, y_ditch = ditch.line.xy
                min_x, max_x = min(x_ditch), max(x_ditch)
                min_y, max_y = min(y_ditch), max(y_ditch)
                view_bbox = (min_x - 8000, min_y - 8000, max_x + 8000, max_y + 8000)

                fig, ax = plt.subplots(figsize=(18, 12))

                # 1. 基础背景
                ax.plot(*centerline.xy, color="gray", linewidth=1.5, label="中心线")
                ax.plot(*right_line.xy, color="#1f77b4", linewidth=2, label="右岸线")
                ax.plot(*left_line.xy, color="#d62728", linewidth=2, label="左岸线")
                ax.plot(*dam_line.xy, color="orange", linewidth=2, label="堤坝线")
                ax.plot(x_ditch, y_ditch, color="blue", linewidth=2.5, zorder=5, label=f"清沟: {ditch.id}")

                # 绘制子线段高亮 (只绘制堤坝线)
                if dam_length > 0:
                    seg = extract_subcurve(dam_line, proj_start_dam_point, proj_end_dam_point)
                    ax.plot(*seg.xy, color="#994D00", linewidth=2.5, zorder=6, label="堤坝线子线段")

                if manual_geom:
                    if manual_geom.geom_type == 'MultiLineString':
                        for line in manual_geom.geoms:
                            ax.plot(*line.xy, color="black", linewidth=2.5, zorder=6)
                        ax.plot([], [], color="black", linewidth=2.5, zorder=6, label="人工投影")
                    else:
                        ax.plot(*manual_geom.xy, color="black", linewidth=2.5, zorder=6, label="人工投影")

                # 更新文本内容
                text_content = (
                    f"长度 (米):\n"
                    f"  - 清沟实际: {ditch_length:.2f}\n"
                    f"  - 堤坝线投影: {dam_length:.2f}\n"
                )
                if manual_geom:
                    text_content += f"  - 人工投影: {manual_length:.2f}"

                props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.7)
                ax.text(0.02, 0.98, text_content, transform=ax.transAxes, fontsize=12,
                        verticalalignment='top', bbox=props)

                ax.set_xlim(view_bbox[0], view_bbox[2])
                ax.set_ylim(view_bbox[1], view_bbox[3])
                ax.set_aspect('equal', adjustable='box')
                ax.grid(True)
                ax.legend(loc='lower left')
                ax.set_title(f"{safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__base.png"),
                            dpi=120, bbox_inches='tight')

                # 2. 投影线版 (只绘制到堤坝线)
                if dam_length > 0:
                    ax.plot([start_point.x, proj_start_dam_point.x], [start_point.y, proj_start_dam_point.y],
                            '--', color='darkorange', linewidth=1.2)
                    ax.plot([end_point.x, proj_end_dam_point.x], [end_point.y, proj_end_dam_point.y],
                            '--', color='darkorange', linewidth=1.2)

                ax.scatter([start_point.x, end_point.x],
                           [start_point.y, end_point.y],
                           color='purple', s=50, zorder=6)

                ax.set_title(f"投影关系 - {safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__proj.png"),
                            dpi=120, bbox_inches='tight')

                # 3. 封闭图形版 (逻辑不变)
                visible_shape_indices = list(idx_shapes.intersection(view_bbox))
                for j in visible_shape_indices:
                    shape = closed_shapes[j]
                    px, py = shape.polygon.exterior.xy
                    color = '#' + hashlib.md5(str(j).encode()).hexdigest()[:6]
                    ax.fill(px, py, color=color, alpha=0.25)
                    ax.plot(px, py, color="black", linewidth=0.6, alpha=0.5)
                ax.set_title(f"封闭区域 - {safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__closed.png"),
                            dpi=120, bbox_inches='tight')

                plt.close(fig)

    # --- 保存 SHP (逻辑不变) ---
    if save_path and all_geometries_for_shp:
        print("\n正在将所有处理结果保存到 SHP 文件...")
        try:
            df = pd.DataFrame(all_geometries_for_shp)
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:32650")
            shp_output_path = os.path.join(save_path, "processed_ditches_with_projections.shp")
            gdf.to_file(shp_output_path, driver='ESRI Shapefile', encoding='utf-8')
            print(f"✅ 所有清沟处理结果已成功保存到: {shp_output_path}")
        except Exception as e:
            print(f"⚠️ 保存 SHP 文件时发生错误: {e}")

    return

def plot_debug_point_outside_shapes(
    point_to_check: Point,
    all_closed_shapes: list,
    ditch_line: LineString, # 新增参数：接收整条清沟的线数据
    ditch_info: str,
    point_type: str,
    save_path: str
):
    """
    当一个点在所有封闭区域之外时，生成一张以该点所在清沟为中心的调试图。
    """
    fig, ax = plt.subplots(figsize=(16, 10))

    # 1. 绘制所有的封闭区域作为背景
    for shape in all_closed_shapes:
        px, py = shape.polygon.exterior.xy
        ax.plot(px, py, 'b-', linewidth=1, alpha=0.5)
        ax.fill(px, py, 'lightblue', alpha=0.3)

    # 2. 绘制整条有问题的清沟，以提供上下文
    ax.plot(*ditch_line.xy, color='orange', linewidth=3, zorder=9, label=f'问题清沟 (Ditch ID: {ditch_info})')

    # 3. 用醒目的标记高亮显示有问题的端点
    ax.scatter(
        [point_to_check.x], [point_to_check.y],
        color='red',
        zorder=10,
        label=f'未找到区域的{point_type} (Problematic Point)'
    )

    # --- 4.【核心修改】根据清沟的范围和指定的缓冲距离，设置视图 ---
    buffer = 8000  # 您要求的 8000 米缓冲
    min_x, min_y, max_x, max_y = ditch_line.bounds
    ax.set_xlim(min_x - buffer, max_x + buffer)
    ax.set_ylim(min_y - buffer, max_y + buffer)

    # 5. 添加图表信息
    title = f"调试图: 清沟 '{ditch_info}' 的 {point_type}\n未能找到所在的封闭区域"
    ax.set_title(title, fontsize=16, color='red')
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_aspect('equal', adjustable='box')

    # 6. 保存并显示
    print(f"    -> 正在保存调试图到: {save_path}")
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close(fig)