from shapely.geometry import Polygon, LineString, Point
from shapely.ops import substring
from tqdm import tqdm
from geometry.close_shape import ClosedShape
from processing.splitting import extract_subcurve


def split_shape_if_needed(upper_segment, lower_segment, meters, current_above, current_below, next_above, next_below, log=False):
    """
    递归拆分超过指定长度的封闭形状。
    """
    upper_length = upper_segment.length
    lower_length = lower_segment.length

    # 如果上边界或下边界长度超过限制，则拆分
    if upper_length > meters or lower_length > meters:
        # 计算北岸、南岸的中点
        mid_upper = upper_segment.interpolate(0.5, normalized=True)
        mid_lower = lower_segment.interpolate(0.5, normalized=True)

        # 递归拆分左半部分
        left_upper = extract_subcurve(upper_segment, current_above, mid_upper, log=log)
        left_lower = extract_subcurve(lower_segment, mid_lower, current_below, log=log)
        left_shapes = split_shape_if_needed(
            left_upper, left_lower, meters,
            current_above, current_below, mid_upper, mid_lower, log
        )

        # 递归拆分右半部分
        right_upper = extract_subcurve(upper_segment, mid_upper, next_above, log=log)
        right_lower = extract_subcurve(lower_segment, next_below, mid_lower, log=log)
        right_shapes = split_shape_if_needed(
            right_upper, right_lower, meters,
            mid_upper, mid_lower, next_above, next_below, log
        )

        return left_shapes + right_shapes
    else:
        # 不需要拆分，直接返回当前形状
        polygon_coords = [
            (current_above.x, current_above.y),
            *list(upper_segment.coords),
            (next_above.x, next_above.y),
            (next_below.x, next_below.y),
            *list(lower_segment.coords),
            (current_below.x, current_below.y),
            (current_above.x, current_above.y)
        ]
        polygon = Polygon(polygon_coords)
        return [ClosedShape(
            intersections=polygon_coords,
            work_line_1=LineString([current_above, current_below]),
            work_line_2=LineString([next_above, next_below]),
            tangent_line_1=upper_segment,
            tangent_line_2=lower_segment,
            polygon=polygon
        )]


def generate_closed_shapes_with_polylines(center_normals, north_line, south_line, meters, log=False):
    """
    生成封闭形状，并对超过 meters 长度的形状进行拆分。
    """
    closed_shapes = []
    for i in tqdm(range(len(center_normals) - 1), desc="生成封闭形状", unit="个"):
        current_point = center_normals[i][0]
        next_point = center_normals[i + 1][0]

        current_normal = center_normals[i][1].coords
        next_normal = center_normals[i + 1][1].coords

        current_above = Point(current_normal[0][0], current_normal[0][1])  # 北
        current_below = Point(current_normal[1][0], current_normal[1][1])  # 南
        next_above = Point(next_normal[0][0], next_normal[0][1])  # 北
        next_below = Point(next_normal[1][0], next_normal[1][1])  # 南

        upper_segment = extract_subcurve(north_line, current_above, next_above, log=log)
        lower_segment = extract_subcurve(south_line, next_below, current_below, log=log)

        closed_shapes.extend(
            split_shape_if_needed(upper_segment, lower_segment, meters,
                                  current_above, current_below, next_above, next_below, log)
        )

    return closed_shapes
