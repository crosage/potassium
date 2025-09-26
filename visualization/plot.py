"""
该模块提供了多段线、法线、封闭形状等数据的可视化展示功能，支持在操作结束后使用 matplotlib 进行结果展示。
"""
import hashlib
from rtree import index as rindex
import matplotlib.pyplot as plt
from matplotlib import rcParams
from shapely import STRtree
from shapely.geometry import Point, LineString, Polygon, box


def set_equal_aspect_ratio():
    """
    设置 Matplotlib 图表的横纵坐标比例为相等，避免出现拉伸。
    """
    plt.gca().set_aspect('equal', adjustable='box')


def plot_cropping_results(
        original_centerline: LineString,
        original_north_line: LineString,
        original_south_line: LineString,
        cropped_centerline: LineString,
        cropped_north_line: LineString,
        cropped_south_line: LineString,
        title="Smart Cropping Results",
        save_path=None
):
    """
    可视化智能裁剪的结果，对比裁剪前后的线条。

    Args:
        original_centerline (LineString): 原始中心线。
        original_north_line (LineString): 原始北岸线。
        original_south_line (LineString): 原始南岸线。
        cropped_centerline (LineString): 裁剪后的中心线。
        cropped_north_line (LineString): 裁剪后的北岸线。
        cropped_south_line (LineString): 裁剪后的南岸线。
        title (str, optional): 图像标题.
        save_path (str, optional): 图像保存路径. 如果提供，则保存图像.
    """
    fig, ax = plt.subplots(figsize=(20, 12))

    # --- 1. 绘制原始线条 (作为背景，使用虚线和较浅的颜色) ---
    ax.plot(*original_centerline.xy, color='gray', linestyle='--', linewidth=1.5,
            label='原始中心线 (Original Centerline)')
    ax.plot(*original_north_line.xy, color='lightcoral', linestyle='--', linewidth=1.5,
            label='原始北岸线 (Original North Line)')
    ax.plot(*original_south_line.xy, color='lightskyblue', linestyle='--', linewidth=1.5,
            label='原始南岸线 (Original South Line)')

    # --- 2. 绘制裁剪后的线条 (突出显示，使用实线和更醒目的颜色) ---
    ax.plot(*cropped_centerline.xy, color='black', label='裁剪后中心线 (Cropped Centerline)')
    ax.plot(*cropped_north_line.xy, color='red', label='裁剪后北岸线 (Cropped North Line)')
    ax.plot(*cropped_south_line.xy, color='blue', label='裁剪后南岸线 (Cropped South Line)')

    # --- 3. 标记出裁剪的起终点，使其更清晰 ---
    start_point = cropped_centerline.boundary.geoms[0]
    end_point = cropped_centerline.boundary.geoms[1]
    ax.scatter([start_point.x], [start_point.y], color='green', s=150, zorder=5, label='共同起点 (Common Start)')
    ax.scatter([end_point.x], [end_point.y], color='magenta', s=150, zorder=5, label='共同终点 (Common End)')

    # --- 4. 设置图表属性 ---
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.legend(loc='best')
    ax.grid(True, linestyle='-', alpha=0.6)
    ax.set_aspect('equal', adjustable='box')  # 保证地理坐标系比例正确

    # --- 5. 保存和显示 ---
    if save_path:
        print(f"正在保存裁剪结果对比图到: {save_path}")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    plt.show()
    plt.close(fig)  # 关闭图形，释放内存
def plot_polyline(polyline, title="Polyline Visualization"):
    """
    绘制单条多段线。
    """
    if not polyline:
        print("没有多段线可展示。")
        return

    points = polyline.points if hasattr(polyline, 'points') else polyline['points']
    x = [point.x for point in points]
    y = [point.y for point in points]

    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='b', label='Polyline')
    plt.scatter(x[0], y[0], color='g', label='Start Point')
    plt.scatter(x[-1], y[-1], color='r', label='End Point')

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_multiple_polylines(polylines, title="Multiple Polylines Visualization"):
    """
    绘制多条多段线。
    """
    if not polylines:
        print("没有多段线可展示。")
        return

    plt.figure(figsize=(12, 8))

    for idx, polyline in enumerate(polylines):
        points = polyline.points if hasattr(polyline, 'points') else polyline['points']
        x = [point.x for point in points]
        y = [point.y for point in points]
        plt.plot(x, y, marker='o', linestyle='-', label=f'Polyline {idx + 1}')

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_split_lines(north_line, south_line, title="Split Lines Visualization"):
    """
    绘制分割后的北线和南线。
    """
    if not north_line or not south_line:
        print("没有分割线可展示。")
        return

    plt.figure(figsize=(12, 8))

    # 绘制北线
    x_north, y_north = zip(*north_line.coords)
    plt.plot(x_north, y_north, marker='o', color='red', label='North Line')

    # 绘制南线
    x_south, y_south = zip(*south_line.coords)
    plt.plot(x_south, y_south, marker='o', color='green', label='South Line')

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()
from typing import Optional, List, Tuple


rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']  # 黑体、微软雅黑
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
def _build_point_rtree(points: List[Point]):
    """用点的包围盒构建 R 树（坐标退化为 x,y,x,y）。"""
    idx = rindex.Index()
    for i, p in enumerate(points):
        x, y = p.x, p.y
        idx.insert(i, (x, y, x, y))
    return idx

def _build_line_rtree(lines: List[LineString]):
    """（可选）用线的外包矩形构建 R 树，适合按“线是否进入视窗”筛选。"""
    idx = rindex.Index()
    for i, ln in enumerate(lines):
        minx, miny, maxx, maxy = ln.bounds
        idx.insert(i, (minx, miny, maxx, maxy))
    return idx


def plot_normals(
    normals: List[Tuple[Point, LineString]],
    north_line: LineString, south_line: LineString, center_line: LineString,
    x_min: Optional[float] = None, x_max: Optional[float] = None,
    y_min: Optional[float] = None, y_max: Optional[float] = None,
    rtree_mode: str = "point"  # "point" 用法线起点建树；"line" 用整条线的 bounds 建树
):
    fig, ax = plt.subplots(figsize=(10, 8))

    # --- 画中心线与边界 ---
    x_center, y_center = center_line.xy
    ax.plot(x_center, y_center, color='gray', linewidth=2, label='中心线')

    x_north, y_north = north_line.xy
    ax.plot(x_north, y_north, color='red', label='左岸线')
    x_south, y_south = south_line.xy
    ax.plot(x_south, y_south, color='green', label='右岸线')

    # --- 基本检查 ---
    if not normals or not (isinstance(normals[0], tuple) and len(normals[0]) == 2
                           and isinstance(normals[0][0], Point) and isinstance(normals[0][1], LineString)):
        print("警告：法线数据格式可能不符合预期，或列表为空，请检查数据。")
        plt.tight_layout(); plt.show()
        return

    # --- 决定绘制集合：若给定范围，用 R 树筛；否则全量 ---
    selected_indices = range(len(normals))
    if None not in (x_min, x_max, y_min, y_max):
        bbox = (x_min, y_min, x_max, y_max)

        if rtree_mode == "line":
            # 用整条线的包围盒建树，更严格：只画包围盒与视窗相交的法线
            lines = [ln for _, ln in normals]
            idx = _build_line_rtree(lines)
        else:
            # 默认：用法线在中心线上的落点建树，最快
            points = [p for p, _ in normals]
            idx = _build_point_rtree(points)

        # 命中索引（整数），已是原列表索引
        selected_indices = list(idx.intersection(bbox))

    # --- 绘制筛选后的法线 ---
    for idx_i, i in enumerate(selected_indices):
        normal_point, normal_line = normals[i]
        x_normal, y_normal = normal_line.xy
        ax.plot(x_normal, y_normal, color='purple', linewidth=0.5,
                label='法线' if idx_i == 0 else "_nolegend_")
        ax.scatter(normal_point.x, normal_point.y, marker='o', color='blue', s=10,
                   label='法线起点' if idx_i == 0 else "_nolegend_")

    # --- 视图与外观 ---
    ax.set_xlabel("X 坐标"); ax.set_ylabel("Y 坐标")
    title = "法线与边界线示意图"
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.legend(loc='best'); ax.grid(True); ax.set_aspect('equal')

    if None not in (x_min, x_max): ax.set_xlim(x_min, x_max)
    if None not in (y_min, y_max): ax.set_ylim(y_min, y_max)

    plt.tight_layout()
    plt.show()

def plot_closed_shapes(
    closed_shapes, north_line, south_line, center_line,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    y_min: Optional[float] = None,
    y_max: Optional[float] = None
):
    fig, ax = plt.subplots(figsize=(12, 8))

    # 绘制中心线
    x_center, y_center = center_line.xy
    ax.plot(x_center, y_center, color="gray", linewidth=2, label="中心线")

    # 绘制左岸线
    x_north, y_north = north_line.xy
    ax.plot(x_north, y_north, color='red', linestyle='--', label='左岸线')

    # 绘制右岸线
    x_south, y_south = south_line.xy
    ax.plot(x_south, y_south, color='green', linestyle='--', label='右岸线')

    # 绘制封闭形状
    if closed_shapes:
        for j, shape_obj in enumerate(closed_shapes):
            if hasattr(shape_obj, 'polygon') and isinstance(shape_obj.polygon, Polygon):
                polygon = shape_obj.polygon
                hash_input = str(j).encode('utf-8')
                hash_digest = hashlib.md5(hash_input).hexdigest()
                color = '#' + hash_digest[:6]
                px, py = polygon.exterior.xy
                ax.fill(px, py, color=color, alpha=0.5, label='剖分区域' if j == 0 else "_nolegend_")
                ax.plot(px, py, color="black", linewidth=0.7)
            else:
                 print(f"警告：索引 {j} 的 closed_shapes 元素没有有效的 polygon 属性。")

    # 坐标轴中文标签
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")

    # 标题
    title = "河道剖分示意图"
    ax.set_title(title, fontsize=16, fontweight='bold')

    # 其他图形参数
    ax.legend(loc='best')
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')

    # 视窗范围
    if x_min is not None and x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)

    plt.tight_layout()
    plt.show()