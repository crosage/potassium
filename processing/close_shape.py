import hashlib
import os

from matplotlib import pyplot as plt
from shapely import Polygon
from shapely.geometry import LineString, Point

from geometry.close_shape import ClosedShape
from processing.splitting import extract_subcurve


def plot_closed_shapes_with_polylines(center_normals, north_line, south_line, log=False):
    """
    给定中心点、北岸和南岸折线，求出每个封闭的区域。
    :param center_normals: 中心点及法线数据。
    :param north_line: 北岸折线（上方折线）。
    :param south_line: 南岸折线（下方折线）。
    :param original_line: 原始中心线（用于计算真实切线方向）。
    :param log: 是否绘制调试过程。
    :return: 封闭形状列表。
    """
    closed_shapes = []
    for i in range(len(center_normals) - 1):
        print(f"当前正在遍历 {i}")

        # 当前点与下一个点
        current_point = center_normals[i][0]
        next_point = center_normals[i + 1][0]

        # 当前法线与下一个法线的点
        current_normal = center_normals[i][1].coords
        next_normal = center_normals[i + 1][1].coords

        # 提取法线点
        current_above = Point(current_normal[0][0], current_normal[0][1]) # 北
        current_below = Point(current_normal[1][0], current_normal[1][1]) # 南
        next_above = Point(next_normal[0][0], next_normal[0][1]) # 北
        next_below = Point(next_normal[1][0], next_normal[1][1]) # 南

        # 提取北岸（上方）和南岸（下方）的子曲线
        upper_segment = extract_subcurve(north_line, current_above, next_above, log=log)
        lower_segment = extract_subcurve(south_line, next_below, current_below, log=log)

        # 构建封闭多边形
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

        closed_shapes.append(ClosedShape(
            intersections=polygon_coords,
            work_line_1=LineString([current_above, current_below]),
            work_line_2=LineString([next_above, next_below]),
            tangent_line_1=upper_segment,
            tangent_line_2=lower_segment,
            polygon=polygon
        ))
    return closed_shapes