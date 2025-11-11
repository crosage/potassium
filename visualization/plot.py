"""
该模块提供了多段线、法线、封闭形状等数据的可视化展示功能，支持在操作结束后使用 matplotlib 进行结果展示。
"""
import hashlib
import os
from rtree import index as rindex
from shapely.geometry import Point, LineString, Polygon, box
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from typing import Union, Optional, Iterable
from shapely.geometry import LineString, MultiLineString
from shapely.geometry.base import BaseGeometry
from matplotlib import rcParams, patheffects


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
from typing import Optional, List, Tuple, Union, Iterable

rcParams['font.family'] = ['serif']
rcParams['font.serif'] = ['SimSun', 'NSimSun', 'Songti SC', 'STSong', 'Source Han Serif SC', 'Noto Serif CJK SC', 'AR PL UMing CN']
rcParams['axes.unicode_minus'] = False
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
    ax.plot(x_north, y_north, color='red', label='大堤线')
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
    ax.plot(x_north, y_north, color='red', linestyle='--', label='大堤线')

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


def _iter_line_geoms(geoms):
    """通用迭代器：接受单个或列表，兼容 GeoSeries/GeoDataFrame/Polygon/MultiPolygon 转边界"""

    def _yield_lines(g):
        if g is None:
            return

        # ✅ 优先处理 GeoSeries / GeoDataFrame
        if isinstance(g, (gpd.GeoSeries, gpd.GeoDataFrame)):
            for geom in g.geometry if hasattr(g, 'geometry') else g:
                for ln in _yield_lines(geom):
                    yield ln
            return

        # 处理单个几何对象
        g = getattr(g, 'geometry', g)
        gt = getattr(g, 'geom_type', None)

        if gt == 'LineString' or gt == 'LinearRing':
            yield g
        elif gt == 'MultiLineString':
            for ln in g.geoms:
                yield ln
        elif gt == 'Polygon':
            b = g.boundary
            if b.geom_type == 'LineString':
                yield b
            elif b.geom_type == 'MultiLineString':
                for ln in b.geoms:
                    yield ln
        elif gt == 'MultiPolygon':
            for p in g.geoms:
                b = p.boundary
                if b.geom_type == 'LineString':
                    yield b
                elif b.geom_type == 'MultiLineString':
                    for ln in b.geoms:
                        yield ln

    # 主入口
    if isinstance(geoms, (gpd.GeoSeries, gpd.GeoDataFrame)):
        for ln in _yield_lines(geoms):
            yield ln
    elif hasattr(geoms, 'geom_type') or hasattr(geoms, 'geoms'):
        for ln in _yield_lines(geoms):
            yield ln
    elif hasattr(geoms, '__iter__') and not isinstance(geoms, (str, bytes)):
        for g in geoms:
            for ln in _yield_lines(g):
                yield ln
    else:
        for ln in _yield_lines(geoms):
            yield ln

def _union_bounds(*geoms_groups):
    """返回所有输入线的联合 bounds: (minx, miny, maxx, maxy)。若为空返回 None。"""
    has_any = False
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for geoms in geoms_groups:
        for ln in _iter_line_geoms(geoms):
            x0, y0, x1, y1 = ln.bounds
            if x0 < minx: minx = x0
            if y0 < miny: miny = y0
            if x1 > maxx: maxx = x1
            if y1 > maxy: maxy = y1
            has_any = True
    return (minx, miny, maxx, maxy) if has_any else None

def plot_river_elements(
    dam_line: Union[LineString, Iterable[BaseGeometry]],
    left_line: Union[LineString, Iterable[BaseGeometry]],
    right_line: Union[LineString, Iterable[BaseGeometry]],
    ditches: Union[Iterable[BaseGeometry], BaseGeometry],
    center_line: Optional[Union[LineString, Iterable[BaseGeometry]]] = None,
    title: str = "大堤线 / 左右岸线 / 清沟 总览",
    # 如果提供 bbox 就用；否则自动拟合全范围
    x_min: Optional[float] = None, x_max: Optional[float] = None,
    y_min: Optional[float] = None, y_max: Optional[float] = None,
    save_path: Optional[str] = None,
    auto_figsize: bool = True,     # ✅ 根据数据长宽比自动设定画布尺寸
    base_figsize_width: float = 16, # 以宽度为基准，自适应高度
    padding_ratio: float = 0.02,    # 视窗留白比例（2%）
):
    # --- 1) 计算联合范围（如果未指定 bbox） ---
    if None in (x_min, x_max, y_min, y_max):
        bounds = _union_bounds(dam_line, right_line, ditches, center_line)
        if bounds is not None:
            bx0, by0, bx1, by1 = bounds
            dx = max(bx1 - bx0, 1e-9)
            dy = max(by1 - by0, 1e-9)
            pad_x = dx * padding_ratio
            pad_y = dy * padding_ratio
            x_min, x_max = bx0 - pad_x, bx1 + pad_x
            y_min, y_max = by0 - pad_y, by1 + pad_y
        else:
            # 没有数据，给个默认范围
            x_min, x_max, y_min, y_max = 0, 1, 0, 1

    # --- 2) 依据数据比例自适应画布大小（避免“看起来挤压”） ---
    if auto_figsize:
        width = float(x_max - x_min)
        height = float(y_max - y_min)
        aspect = width / height if height > 0 else 1.0
        figsize = (base_figsize_width, max(base_figsize_width / max(aspect, 1e-6), 4.0))
    else:
        figsize = (16, 10)

    fig, ax = plt.subplots(figsize=figsize)

    # 3) 画中心线（可选）
    if center_line is not None:
        first = True
        for ln in _iter_line_geoms(center_line):
            x, y = ln.xy
            ax.plot(x, y, color='gray', linewidth=2, label='中心线' if first else "_nolegend_")
            first = False

    # 4) 大堤线
    first = True
    for ln in _iter_line_geoms(dam_line):
        x, y = ln.xy
        ax.plot(x, y, color='orange', linewidth=2.2, label='大堤线' if first else "_nolegend_")
        first = False

    # # 5) 左岸线
    first = True
    for ln in _iter_line_geoms(left_line):
        x, y = ln.xy
        ax.plot(x, y, color='red', linewidth=1.8, label='左岸线' if first else "_nolegend_")
        first = False

    # 6) 右岸线
    first = True
    for ln in _iter_line_geoms(right_line):
        x, y = ln.xy
        ax.plot(x, y, color='green', linewidth=1.8, label='右岸线' if first else "_nolegend_")
        first = False

    first = True
    count_ditch = 0

    # 若 ditches 是单个对象，转为列表方便遍历
    if hasattr(ditches, "line"):
        ditches = [ditches]

    for ditch in ditches:
        try:
            # ditch.line 应该是 shapely.geometry.LineString
            x_ditch, y_ditch = ditch.line.xy
            ax.plot(
                x_ditch, y_ditch,
                color='blue',
                linewidth=2.0,  # 稍微粗一点，论文可视化更清晰
                alpha=0.85,
                zorder=6,
                label='清沟' if first else "_nolegend_"
            )
            first = False
            count_ditch += 1
        except Exception as e:
            print(f"⚠️ 无法绘制清沟对象 {getattr(ditch, 'attributes', '')}: {e}")

    # 若一个清沟都没画出来，也要确保图例里仍然出现“清沟”
    if count_ditch == 0:
        ax.plot([], [], color='blue', linewidth=2.0, label='清沟')
        print("⚠️ 未绘制任何清沟线，已添加图例占位符。")

    # --- 外观与比例控制 ---
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel("X 坐标"); ax.set_ylabel("Y 坐标")
    ax.grid(True, alpha=0.5)
    ax.set_aspect('equal', adjustable='box')  # ✅ 等比例，不畸变
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.legend(loc='best')

    plt.tight_layout()
    if save_path:
        print(f"正在保存总览图到: {save_path}")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


from matplotlib.ticker import FuncFormatter


def plot_river_with_satellite(
        left_line: Union[LineString, Iterable[BaseGeometry]],
        right_line: Union[LineString, Iterable[BaseGeometry]],
        ditches: Union[Iterable[BaseGeometry], BaseGeometry],
        center_line: Optional[Union[LineString, Iterable[BaseGeometry]]] = None,
        title: str = "黄河研究区域卫星影像图",
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        y_min: Optional[float] = None,
        y_max: Optional[float] = None,
        save_path: Optional[str] = None,
        save_clean_path: Optional[str] = None,  # ✅ 纯卫星底图，无矢量线
        auto_figsize: bool = True,
        base_figsize_width: float = 24,
        padding_ratio: float = 0.02,
        use_proxy: bool = True,
        proxy_url: str = 'http://127.0.0.1:7890',
        satellite_source: str = 'esri',
        dpi: int = 300,
        font_family: str = 'SimSun',
        show_axis: bool = True,
):
    """
    绘制带有卫星底图的河道要素图

    参数:
        save_path: 保存完整版（带矢量线、标题、图例等）
        save_clean_path: 保存纯卫星底图（无矢量线、无装饰）
    """

    # ====== 设置代理 ======
    if use_proxy:
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
        print(f"✅ 已设置代理: {proxy_url}")

    # ====== 设置字体 ======
    rcParams['font.family'] = ['serif']
    rcParams['font.serif'] = [font_family, 'SimSun', 'NSimSun', 'Songti SC', 'STSong']
    rcParams['axes.unicode_minus'] = False

    # --- 1) 转换到 Web Mercator (EPSG:3857) ---
    print("正在转换坐标系到 Web Mercator (EPSG:3857)...")

    def to_web_mercator(geom_input):
        """将几何对象转换为 Web Mercator"""
        if geom_input is None:
            return None

        if isinstance(geom_input, (gpd.GeoDataFrame, gpd.GeoSeries)):
            if geom_input.crs is None:
                geom_input = geom_input.set_crs('EPSG:32649')
            return geom_input.to_crs(epsg=3857)

        if isinstance(geom_input, (LineString, MultiLineString)):
            gs = gpd.GeoSeries([geom_input], crs='EPSG:32649')
            return gs.to_crs(epsg=3857)

        if hasattr(geom_input, '__iter__') and not isinstance(geom_input, (str, bytes)):
            try:
                lines = []
                for item in geom_input:
                    if hasattr(item, 'line'):
                        lines.append(item.line)
                    elif isinstance(item, (LineString, MultiLineString)):
                        lines.append(item)
                if lines:
                    gs = gpd.GeoSeries(lines, crs='EPSG:32649')
                    return gs.to_crs(epsg=3857)
            except Exception as e:
                print(f"⚠️ 转换对象列表时出错: {e}")

        return geom_input

    left_line_web = to_web_mercator(left_line)
    right_line_web = to_web_mercator(right_line)
    ditches_web = to_web_mercator(ditches)
    center_line_web = to_web_mercator(center_line) if center_line is not None else None

    # --- 2) 计算联合范围（不包含左岸线） ---
    if None in (x_min, x_max, y_min, y_max):
        print("正在计算数据边界（不包含左岸线）...")
        bounds = _union_bounds(left_line_web, right_line_web, ditches_web, center_line_web)
        if bounds is not None:
            bx0, by0, bx1, by1 = bounds
            dx = max(bx1 - bx0, 1e-9)
            dy = max(by1 - by0, 1e-9)
            pad_x = dx * padding_ratio
            pad_y = dy * padding_ratio
            x_min, x_max = bx0 - pad_x, bx1 + pad_x
            y_min, y_max = by0 - pad_y, by1 + pad_y
        else:
            x_min, x_max, y_min, y_max = 0, 1, 0, 1

    # --- 3) 依据数据比例自适应画布大小 ---
    if auto_figsize:
        width = float(x_max - x_min)
        height = float(y_max - y_min)
        aspect = width / height if height > 0 else 1.0
        figsize = (base_figsize_width, max(base_figsize_width / max(aspect, 1e-6), 4.0))
    else:
        figsize = (24, 16)

    # ========================================
    # ✅ 先生成纯卫星底图（如果需要）
    # ========================================
    if save_clean_path:
        print("\n" + "=" * 50)
        print("正在生成纯卫星底图（无矢量线）...")
        print("=" * 50)

        fig_clean, ax_clean = plt.subplots(figsize=figsize)
        ax_clean.set_xlim(x_min, x_max)
        ax_clean.set_ylim(y_min, y_max)
        ax_clean.set_aspect('equal', adjustable='box')

        # 只加载卫星底图
        try:
            if satellite_source.lower() == 'esri':
                cx.add_basemap(ax_clean, source=cx.providers.Esri.WorldImagery,
                               zoom='auto', attribution=False)
                print("✅ 纯卫星底图加载成功")
            elif satellite_source.lower() == 'carto':
                cx.add_basemap(ax_clean,
                               source='https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
                               zoom='auto', attribution=False)
                print("✅ 纯卫星底图加载成功")
        except Exception as e:
            print(f"⚠️ 纯底图加载失败: {e}")

        # 移除所有装饰
        ax_clean.axis('off')

        # 保存纯底图
        save_dir = os.path.dirname(save_clean_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_clean_path, dpi=dpi, bbox_inches='tight',
                    facecolor='white', pad_inches=0)
        print(f"✅ 纯卫星底图已保存至: {save_clean_path}\n")
        plt.close(fig_clean)

    # ========================================
    # 生成带矢量线的完整版
    # ========================================
    print("正在生成带矢量线的完整版...")
    fig, ax = plt.subplots(figsize=figsize)

    # --- 4) 设置坐标范围 ---
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal', adjustable='box')

    # --- 5) 绘制矢量要素 ---
    print("正在绘制矢量要素...")

    def plot_geom(geom_input, color, linewidth, label, zorder=5, alpha=0.9):
        """通用绘制函数"""
        first = True
        for ln in _iter_line_geoms(geom_input):
            x, y = ln.xy
            ax.plot(x, y, color=color, linewidth=linewidth,
                    label=label if first else '_nolegend_',
                    zorder=zorder, alpha=alpha)
            first = False


    if left_line_web is not None:
        plot_geom(left_line_web, 'orange', 1.5, '左岸大堤线', zorder=4, alpha=0.8)

    if right_line_web is not None:
        plot_geom(right_line_web, 'green', 1.5, '右岸大堤线', zorder=4, alpha=0.8)

    if center_line_web is not None:
        plot_geom(center_line_web, 'blue', 2, '河道中心线', zorder=6, alpha=0.9)

    # 清沟特殊处理
    count_ditch = 0
    if ditches_web is not None:
        first = True
        for ln in _iter_line_geoms(ditches_web):
            x, y = ln.xy
            ax.plot(x, y, color='cyan', linewidth=3,
                    label='清沟' if first else '_nolegend_',
                    zorder=7, alpha=1.0)
            first = False
            count_ditch += 1

    if count_ditch == 0:
        ax.plot([], [], color='cyan', linewidth=3, label='清沟')
        print("⚠️ 未绘制任何清沟线，已添加图例占位符。")

    # --- 6) 添加卫星底图 ---
    print("正在加载卫星底图...")
    try:
        if satellite_source.lower() == 'esri':
            cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery,
                           zoom=10, attribution=False)
            print("✅ Esri 卫星底图加载成功")
        elif satellite_source.lower() == 'carto':
            cx.add_basemap(ax,
                           source='https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
                           zoom='auto', attribution=False)
            print("✅ CartoDB 底图加载成功")
    except Exception as e:
        print(f"⚠️ 底图加载失败: {e}")

    # --- 7) 添加装饰元素 ---
    ax.set_title(title, fontsize=36, fontweight='bold', pad=20)

    if show_axis:
        def format_coord_km(x, pos):
            return f'{x / 1000:.0f}'

        # 坐标标签更大、更粗
        ax.set_xlabel('东向坐标 (千米)', fontsize=26, fontweight='bold', labelpad=12)
        ax.set_ylabel('北向坐标 (千米)', fontsize=26, fontweight='bold', labelpad=12)

        # 坐标轴刻度字体放大、加粗
        ax.tick_params(axis='both', which='major', labelsize=22, width=2, length=8)
        ax.tick_params(axis='both', which='minor', labelsize=18, width=1, length=5)

        ax.xaxis.set_major_formatter(FuncFormatter(format_coord_km))
        ax.yaxis.set_major_formatter(FuncFormatter(format_coord_km))

        # 在卫星底图上提高可读性 —— 给坐标轴文字加白色描边
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_path_effects([
                patheffects.Stroke(linewidth=3, foreground='white'),
                patheffects.Normal()
            ])

        # 更清晰的网格线
        ax.grid(True, color='white', alpha=0.6, linestyle='--', linewidth=0.8)
        ax.axis('on')
    else:
        ax.axis('off')

    ax.legend(loc='upper right', fontsize=18, framealpha=0.9)
    plt.subplots_adjust(top=0.92, right=0.98, left=0.08, bottom=0.08)

    # --- 8) 保存完整版 ---
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        print(f"正在保存完整版图片到: {save_path}")
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', pad_inches=0.3, facecolor='white')
        print(f"✅ 完整版图片已保存")

    plt.show()
    plt.close()