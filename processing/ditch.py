import os
import csv
import hashlib

from pyproj import Geod, Transformer
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import rcParams
import geopandas as gpd
import pandas as pd
from rtree import index  # 空间索引

from processing.splitting import extract_subcurve
from utils.helpers import make_shape_finder

# --- Matplotlib 全局设置 ---
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
rcParams['axes.unicode_minus'] = False
def _center_of_geom(geom):
    # 支持 LineString/Polygon/Point
    c = geom.centroid
    return float(c.x), float(c.y)

def _to_lonlat(x, y, src_crs="EPSG:32650", dst_crs="EPSG:4326"):
    tf = Transformer.from_crs(src_crs, dst_crs, always_xy=True).transform
    lon, lat = tf(x, y)
    return float(lon), float(lat)

def _square_view_bbox_in_degrees(center_geom_src, buffer_m=5000,
                                 source_crs="EPSG:32650", display_crs="EPSG:4326"):
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

def process_ditch_endpoints(ditchs, closed_shapes, north_line, south_line, centerline, save_path=None, log=True):
    """
    高效处理清沟：一次循环绘制三份图（基础版、投影版、封闭版）。
    """
    all_geometries_for_shp = []

    if not save_path:
        log = False

    # --- 创建空间索引 ---
    if log:
        print("正在为背景区域创建空间索引...")
        idx_shapes = index.Index()
        for i, shape in enumerate(closed_shapes):
            idx_shapes.insert(i, shape.polygon.bounds)
        print("✅ 空间索引创建完成。")

    # --- CSV 文件 ---
    if save_path:
        os.makedirs(save_path, exist_ok=True)
        csv_filename = os.path.join(save_path, "ditch_results.csv")
    else:
        csv_filename = "ditch_results.csv"

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "清沟名称(name)", "日期(DATE)", "河流部分(RIVERPART)", "编码(CODE)",
            "清沟实际长度", "南岸投影长度", "北岸投影长度", "中心线投影长度"
        ])

        finder = make_shape_finder(closed_shapes)

        for ditch in tqdm(ditchs, desc="处理所有清沟", unit="条"):
            if len(ditch.points) < 2:
                continue

            start_point, end_point = ditch.points[0], ditch.points[-1]

            # --- 投影点计算 ---
            start_index, start_shape = finder(start_point)
            proj_start_1_point = start_shape.tangent_line_1.interpolate(
                start_shape.tangent_line_1.project(start_point)) if start_shape else None
            proj_start_2_point = start_shape.tangent_line_2.interpolate(
                start_shape.tangent_line_2.project(start_point)) if start_shape else None

            end_index, end_shape = finder(end_point)
            proj_end_1_point = end_shape.tangent_line_1.interpolate(
                end_shape.tangent_line_1.project(end_point)) if end_shape else None
            proj_end_2_point = end_shape.tangent_line_2.interpolate(
                end_shape.tangent_line_2.project(end_point)) if end_shape else None

            proj_start_centerline_point = centerline.line.interpolate(centerline.line.project(start_point))
            proj_end_centerline_point = centerline.line.interpolate(centerline.line.project(end_point))

            # --- 长度计算 ---
            north_length = extract_subcurve(north_line, proj_start_1_point, proj_end_1_point).length \
                if proj_start_1_point and proj_end_1_point else 0
            south_length = extract_subcurve(south_line, proj_start_2_point, proj_end_2_point).length \
                if proj_start_2_point and proj_end_2_point else 0
            ditch_length = ditch.line.length
            centerline_length = extract_subcurve(centerline.line, proj_start_centerline_point,
                                                 proj_end_centerline_point).length

            # --- CSV 保存 ---
            ditch_attributes = ditch.attributes
            csv_writer.writerow([
                ditch_attributes.get('name', 'N/A'), ditch_attributes.get('DATE', 'N/A'),
                ditch_attributes.get('RIVERPART', 'N/A'), ditch_attributes.get('CODE', ditch.id),
                f"{ditch_length:.2f}", f"{south_length:.2f}", f"{north_length:.2f}", f"{centerline_length:.2f}"
            ])

            # --- SHP 记录 ---
            base_record = ditch_attributes.copy()
            base_record.update({
                'ditch_len': ditch_length, 'north_len': north_length,
                'south_len': south_length, 'center_len': centerline_length
            })

            geometries_to_save = {
                'original_ditch': ditch.line,
                'north_projection': extract_subcurve(north_line, proj_start_1_point, proj_end_1_point) if north_length > 0 else None,
                'south_projection': extract_subcurve(south_line, proj_start_2_point, proj_end_2_point) if south_length > 0 else None,
                'center_projection': extract_subcurve(centerline.line, proj_start_centerline_point, proj_end_centerline_point) if centerline_length > 0 else None
            }

            for line_type, geom in geometries_to_save.items():
                if geom and not geom.is_empty:
                    record = base_record.copy()
                    record['line_type'] = line_type
                    record['geometry'] = geom
                    all_geometries_for_shp.append(record)

            # --- 绘图 ---
            if log:
                safe_name = str(ditch_attributes.get('name', 'ditch')).replace('/', '-').replace('\\', '-')
                x_ditch = [p.x for p in ditch.points]
                y_ditch = [p.y for p in ditch.points]
                min_x, max_x = min(x_ditch), max(x_ditch)
                min_y, max_y = min(y_ditch), max(y_ditch)
                view_bbox = (min_x - 5000, min_y - 5000, max_x + 5000, max_y + 5000)

                fig, ax = plt.subplots(figsize=(18, 12))

                # 1. 基础背景
                ax.plot(*centerline.line.xy, color="gray", linewidth=1.5, label="中心线")
                ax.plot(*south_line.xy, color="#1f77b4", linewidth=2, label="南岸线")
                ax.plot(*north_line.xy, color="#d62728", linewidth=2, label="北岸线")
                ax.plot(x_ditch, y_ditch, color="blue", linewidth=3, zorder=5, label=f"清沟: {ditch.id}")

                # 绘制子线段高亮
                if proj_start_1_point and proj_end_1_point:
                    seg = extract_subcurve(north_line, proj_start_1_point, proj_end_1_point)
                    if seg and not seg.is_empty:
                        ax.plot(*seg.xy, color="#660000", linewidth=3, zorder=6, label="北岸子线段")

                if proj_start_2_point and proj_end_2_point:
                    seg = extract_subcurve(south_line, proj_start_2_point, proj_end_2_point)
                    if seg and not seg.is_empty:
                        ax.plot(*seg.xy, color="#003366", linewidth=3, zorder=6, label="南岸子线段")


                if proj_start_centerline_point and proj_end_centerline_point:
                    seg = extract_subcurve(centerline.line, proj_start_centerline_point, proj_end_centerline_point)
                    if seg and not seg.is_empty:
                        ax.plot(*seg.xy, color="#333333", linewidth=3, zorder=6, label="中心线子线段")

                ax.set_xlim(view_bbox[0], view_bbox[2])
                ax.set_ylim(view_bbox[1], view_bbox[3])
                ax.set_aspect('equal', adjustable='box')
                ax.grid(True)
                ax.legend(loc='lower left')
                ax.set_title(f"{safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__base.png"),
                            dpi=120, bbox_inches='tight')

                # 2. 投影线版
                if proj_start_1_point and proj_end_1_point:
                    ax.plot([start_point.x, proj_start_1_point.x],
                            [start_point.y, proj_start_1_point.y],
                            'b--', linewidth=1.2, label="南岸投影起点")
                    ax.plot([end_point.x, proj_end_1_point.x],
                            [end_point.y, proj_end_1_point.y],
                            'b--', linewidth=1.2, label="南岸投影终点")

                if proj_start_2_point and proj_end_2_point:
                    ax.plot([start_point.x, proj_start_2_point.x],
                            [start_point.y, proj_start_2_point.y],
                            'r--', linewidth=1.2, label="北岸投影起点")
                    ax.plot([end_point.x, proj_end_2_point.x],
                            [end_point.y, proj_end_2_point.y],
                            'r--', linewidth=1.2, label="北岸投影终点")

                if proj_start_centerline_point and proj_end_centerline_point:
                    ax.plot([start_point.x, proj_start_centerline_point.x],
                            [start_point.y, proj_start_centerline_point.y],
                            'g--', linewidth=1.2, label="中心线投影起点")
                    ax.plot([end_point.x, proj_end_centerline_point.x],
                            [end_point.y, proj_end_centerline_point.y],
                            'g--', linewidth=1.2, label="中心线投影终点")

                # 起止点标记
                ax.scatter([start_point.x, end_point.x],
                           [start_point.y, end_point.y],
                           color='purple', s=50, zorder=6)

                ax.set_title(f"投影{safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__proj.png"),
                            dpi=120, bbox_inches='tight')

                # 3. 封闭图形版
                visible_shape_indices = list(idx_shapes.intersection(view_bbox))
                for j in visible_shape_indices:
                    shape = closed_shapes[j]
                    px, py = shape.polygon.exterior.xy
                    color = '#' + hashlib.md5(str(j).encode()).hexdigest()[:6]
                    ax.fill(px, py, color=color, alpha=0.25)
                    ax.plot(px, py, color="black", linewidth=0.6, alpha=0.5)
                ax.set_title(f"{safe_name}", fontsize=16)
                plt.savefig(os.path.join(save_path, f"ditch__{safe_name}__{ditch.id}__closed.png"),
                            dpi=120, bbox_inches='tight')

                plt.close(fig)

    # --- 保存 SHP ---
    if save_path and all_geometries_for_shp:
        print("\n正在将所有处理结果保存到 SHP 文件...")
        try:
            df = pd.DataFrame(all_geometries_for_shp)
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:32650")
            shp_output_path = os.path.join(save_path, "processed_ditches_with_projections.shp")
            gdf.to_file(shp_output_path, driver='ESRI Shapefile', encoding='utf-8')
            print(f"所有清沟处理结果已成功保存到: {shp_output_path}")
        except Exception as e:
            print(f"保存 SHP 文件时发生错误: {e}")

    return []
