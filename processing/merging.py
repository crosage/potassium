"""
多段线的合并功能
"""

import matplotlib.pyplot as plt
import random
from geometry.polyline import Polyline


def find_starting_polyline(polylines):
    """
    找到起始多段线。
    """
    min_point = None
    starting_polyline = None
    starting_points = []

    for polyline in polylines:
        for point in [polyline.points[0], polyline.points[-1]]:
            if min_point is None or (point.x < min_point.x or (point.x == min_point.x and point.y < min_point.y)):
                min_point = point
                starting_polyline = polyline
                starting_points = polyline.points if point == polyline.points[0] else list(reversed(polyline.points))

    return starting_polyline, starting_points


def find_closest_polyline(current_end, polylines):
    """
    找到离当前端点最近的多段线。
    """
    min_distance = float('inf')
    closest_polyline = None
    closest_points = []

    for polyline in polylines:
        start_dist = current_end.distance(polyline.points[0])
        end_dist = current_end.distance(polyline.points[-1])

        if start_dist < min_distance:
            min_distance = start_dist
            closest_polyline = polyline
            closest_points = polyline.points  # 正向

        if end_dist < min_distance:
            min_distance = end_dist
            closest_polyline = polyline
            closest_points = list(reversed(polyline.points))  # 反向

    return closest_polyline, closest_points


def merge_polylines(polylines, log=False):
    """
    合并多段线，并可根据 log 参数进行可视化调试。
    """
    if not polylines:
        return None
    for i in polylines:
        print(type(i))
    print(type(polylines))
    starting_polyline, merged_points = find_starting_polyline(polylines)
    remaining_polylines = [p for p in polylines if p != starting_polyline]

    step = 0
    if log:
        plot_polylines_with_labels_and_merged(polylines, merged_points, step)

    while remaining_polylines:
        current_end = merged_points[-1]
        closest_polyline, closest_points = find_closest_polyline(current_end, remaining_polylines)
        print(f"最近的id为{closest_polyline.id} 当前end为{current_end} 端点为{closest_points[0]}和{closest_points[-1]}")

        merged_points.extend(closest_points)
        remaining_polylines.remove(closest_polyline)

        step += 1
        if log:
            plot_polylines_with_labels_and_merged(polylines, merged_points, step)

    merged_polyline = Polyline(id="merged", points=merged_points)
    return merged_polyline


def plot_polylines_with_labels_and_merged(polylines, merged_points=None, step=None):
    """
    可选的多段线可视化调试工具，仅在 log=True 时启用。
    """
    plt.figure(figsize=(12, 12))

    min_x, min_y, max_x, max_y = None, None, None, None
    for polyline in polylines:
        x, y = zip(*[(point.x, point.y) for point in polyline.points])
        min_x = min(min(x), min_x) if min_x is not None else min(x)
        max_x = max(max(x), max_x) if max_x is not None else max(x)
        min_y = min(min(y), min_y) if min_y is not None else min(y)
        max_y = max(max(y), max_y) if max_y is not None else max(y)

    plt.xlim(min_x - 0.1 * (max_x - min_x), max_x + 0.1 * (max_x - min_x))
    plt.ylim(min_y - 0.1 * (max_y - min_y), max_y + 0.1 * (max_y - min_y))

    merged_set = set(merged_points) if merged_points else set()

    for polyline in polylines:
        x, y = zip(*[(point.x, point.y) for point in polyline.points])
        color = (random.random(), random.random(), random.random())

        if not set(polyline.points).issubset(merged_set):
            plt.plot(x, y, color=color, linewidth=1, label=f'Polyline {polyline.id}')
            start_x, start_y = x[0], y[0]
            end_x, end_y = x[-1], y[-1]
            plt.scatter([start_x], [start_y], color=color, s=30, edgecolor='black', zorder=3)
            plt.text(start_x, start_y, f"{polyline.id}", fontsize=10, color=color,
                     ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
        else:
            plt.plot(x, y, color=color, linewidth=1)

    if merged_points:
        x, y = zip(*[(point.x, point.y) for point in merged_points])
        plt.plot(x, y, color='red', linewidth=1.5, label='Merged')

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f'Polylines with Labels - Step {step}' if step is not None else 'Merged Polylines')
    plt.legend()
    plt.show()
