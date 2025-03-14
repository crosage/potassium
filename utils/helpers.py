from matplotlib import pyplot as plt
from rtree import index
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

