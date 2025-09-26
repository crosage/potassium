from matplotlib import pyplot as plt
from rtree import index
from shapely import MultiLineString, GeometryCollection, Polygon
from shapely.geometry import LineString, Point
from shapely.ops import linemerge


def parallel_line_through_point(line, point, distance):
    """
    生成一条与给定线段平行且通过指定点的线。
    """
    if not isinstance(line, LineString):
        raise ValueError("line 参数必须是 LineString 类型")
    if not isinstance(point, Point):
        raise ValueError("point 参数必须是 Point 类型")

    try:
        parallel = line.parallel_offset(distance, 'left')
        if not parallel.is_empty:
            return parallel
        return line.parallel_offset(distance, 'right')
    except Exception as e:
        print(f"生成平行线时发生错误: {e}")
        return LineString()


def find_intersection(line1, line2):
    """
    计算两条线的交点。
    """
    if not isinstance(line1, LineString) or not isinstance(line2, LineString):
        raise ValueError("line1 和 line2 必须是 LineString 类型")

    intersection = line1.intersection(line2)
    if intersection.is_empty:
        return None
    if isinstance(intersection, Point):
        return intersection
    return None


def make_shape_finder(closed_shapes):
    """
    创建并返回一个针对固定封闭形状的查询函数，该函数使用Rtree进行优化。
    """
    # 构建Rtree索引
    idx = index.Index()
    for i, shape in enumerate(closed_shapes):
        # 获取形状的边界框（min_x, min_y, max_x, max_y）
        bbox = shape.polygon.bounds
        idx.insert(i, bbox)

    def find_point(point):
        # 查询点的坐标范围（作为矩形）
        query_bbox = (point.x, point.y, point.x, point.y)
        # 获取所有相交的候选索引
        candidate_indices = idx.intersection(query_bbox)
        # 按原始顺序检查候选形状
        for i in sorted(candidate_indices):
            shape = closed_shapes[i]
            if shape.polygon.contains(point):
                return i, shape
        return None

    return find_point

def merge_lines(lines):
    """
    合并多条线段为一条连续的线。
    """
    try:
        merged = linemerge(lines)
        if isinstance(merged, LineString):
            return merged
        return None
    except Exception as e:
        print(f"合并线段时发生错误: {e}")
        return None


def extract_subcurve_in_polygon_with_debug_plot(line, polygon, ditch_id='Unknown'):
    """
    提取线在多边形内的子曲线，并提供一个matplotlib绘图窗口用于调试。
    """
    # 1. 检查输入是否有效 (代码不变)
    if not line or not polygon or not isinstance(line, LineString) or not isinstance(polygon, Polygon):
        # print(f"*******************************{line} ")
        return None
    if line.is_empty or polygon.is_empty:
        # print("###############################")
        return None

    # 2. 计算交集 (代码不变)
    intersection = line.intersection(polygon)

    # --- 新增的绘图调试部分 ---
    fig, ax = plt.subplots(figsize=(10, 8))

    # 绘制多边形
    px, py = polygon.exterior.xy
    ax.plot(px, py, 'g-', label='Polygon', linewidth=2)
    ax.fill(px, py, 'g', alpha=0.1)

    # 绘制原始的完整曲线
    lx, ly = line.xy
    ax.plot(lx, ly, 'b--', label='Original Line', linewidth=1, alpha=0.8)

    # 绘制交集结果
    if not intersection.is_empty:
        if hasattr(intersection, 'geoms'):  # MultiLineString 或 GeometryCollection
            for geom in intersection.geoms:
                if isinstance(geom, LineString):
                    ix, iy = geom.xy
                    ax.plot(ix, iy, 'r-', label='Intersection', linewidth=3)
        elif isinstance(intersection, LineString):  # LineString
            ix, iy = intersection.xy
            ax.plot(ix, iy, 'r-', label='Intersection', linewidth=3)

    ax.set_title(f"Debug View for Ditch ID: {ditch_id}")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    ax.legend()
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')
    plt.show()  # 显示图像，程序会在此暂停直到你关闭窗口
    # --- 绘图部分结束 ---

    # 3. 处理交集结果 (代码不变)
    if intersection.is_empty:
        return None
    elif isinstance(intersection, (LineString, MultiLineString)):
        return intersection
    elif isinstance(intersection, GeometryCollection):
        lines = [geom for geom in intersection.geoms if isinstance(geom, (LineString, MultiLineString))]
        if not lines: return None
        if len(lines) == 1: return lines[0]
        all_lines = []
        for item in lines:
            if isinstance(item, LineString):
                all_lines.append(item)
            else:
                all_lines.extend(list(item.geoms))
        return MultiLineString(all_lines)
    else:
        return None


def extract_subcurve_in_polygon(line, polygon):
    """
    提取输入线(line)位于多边形(polygon)内部的子曲线部分。

    参数:
    - line (LineString): 原始的完整曲线。
    - polygon (Polygon): 用于裁剪的封闭多边形。

    返回:
    - LineString, MultiLineString, or None: 如果有相交的线段，则返回该线段。
      如果完全不相交或只相交于点，则返回 None。
    """
    # 1. 检查输入是否有效
    if not line or not polygon or not isinstance(line, LineString) or not isinstance(polygon, Polygon):
        print(f"*******************************")
        return None
    if line.is_empty or polygon.is_empty:
        print(f"###############################")
        return None

    # 2. 计算线与多边形的交集
    intersection = line.intersection(polygon)

    # 3. 处理交集结果
    if intersection.is_empty:
        # 情况A: 没有交集
        print("A")
        return None

    elif isinstance(intersection, (LineString, MultiLineString)):
        # 情况B: 理想情况，交集是线或多线
        print("B")
        return intersection

    elif isinstance(intersection, GeometryCollection):
        # 情况C: 交集是多种几何类型的集合（例如，线和点的混合）
        # 我们只提取其中的线状部分
        print("C")
        lines = [geom for geom in intersection.geoms if isinstance(geom, (LineString, MultiLineString))]

        if not lines:
            return None  # 集合中没有线

        # 如果只有一条线，直接返回
        if len(lines) == 1:
            return lines[0]

        # 如果有多条线（通常是MultiLineString），将它们合并
        all_lines = []
        for item in lines:
            if isinstance(item, LineString):
                all_lines.append(item)
            else:  # MultiLineString
                all_lines.extend(list(item.geoms))
        return MultiLineString(all_lines)

    else:
        # 情况D: 交集是点(Point)或多点(MultiPoint)，不是我们需要的“子曲线”
        return None


def distance_between_points(point1, point2):
    """
    计算两点之间的欧几里得距离。
    """
    if not isinstance(point1, Point) or not isinstance(point2, Point):
        raise ValueError("point1 和 point2 必须是 Point 类型")

    return point1.distance(point2)


def normalize_vector(vector):
    """
    对一个向量进行归一化处理。
    """
    import math

    magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
    if magnitude == 0:
        raise ValueError("零向量无法进行归一化")
    return vector[0] / magnitude, vector[1] / magnitude


def midpoint(point1, point2):
    """
    计算两点的中点。
    """
    if not isinstance(point1, Point) or not isinstance(point2, Point):
        raise ValueError("point1 和 point2 必须是 Point 类型")

    mid_x = (point1.x + point2.x) / 2
    mid_y = (point1.y + point2.y) / 2
    return Point(mid_x, mid_y)


def angle_between_vectors(v1, v2):
    """
    计算两个向量之间的夹角。
    """
    import math

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    magnitude_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if magnitude_v1 == 0 or magnitude_v2 == 0:
        raise ValueError("零向量之间无法计算夹角")

    return math.acos(dot_product / (magnitude_v1 * magnitude_v2))

