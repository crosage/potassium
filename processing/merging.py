"""
多段线的合并功能
"""

import matplotlib.pyplot as plt
import random
from geometry.polyline import Polyline


def find_starting_polyline(polylines):
    """
    找到起始多段线（通常选择最左下角的点所在的线）。
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
    找到离当前端点最近的多段线及其正确方向的点列表。
    """
    min_distance = float('inf')
    closest_polyline = None
    best_orientation_is_reversed = False

    for polyline in polylines:
        start_dist = current_end.distance(polyline.points[0])
        if start_dist < min_distance:
            min_distance = start_dist
            closest_polyline = polyline
            best_orientation_is_reversed = False

        end_dist = current_end.distance(polyline.points[-1])
        if end_dist < min_distance:
            min_distance = end_dist
            closest_polyline = polyline
            best_orientation_is_reversed = True

    if closest_polyline is None:
        return None, [], float('inf')

    if best_orientation_is_reversed:
        closest_points = list(reversed(closest_polyline.points))
    else:
        closest_points = closest_polyline.points

    return closest_polyline, closest_points, min_distance


def merge_polylines(polylines, log=False):
    """
    合并多段线（已重构为双向生长算法）。
    """
    if not polylines:
        return None

    polylines_to_process = set(polylines)

    starting_polyline, merged_points = find_starting_polyline(list(polylines_to_process))
    if not starting_polyline:
        return None

    polylines_to_process.remove(starting_polyline)

    step = 0
    if log:
        plot_polylines_with_labels_and_merged(polylines, merged_points, step)

    while polylines_to_process:
        current_start = merged_points[0]
        current_end = merged_points[-1]

        # 寻找连接到尾部的最佳线段
        poly_to_append, points_to_append, dist_to_end = find_closest_polyline(current_end, polylines_to_process)

        # 寻找连接到头部的最佳线段
        poly_to_prepend, points_to_prepend, dist_to_start = find_closest_polyline(current_start, polylines_to_process)

        # 如果找不到任何可以连接的线段，则退出
        if not poly_to_append and not poly_to_prepend:
            break

        # 决定是连接头部还是尾部
        if dist_to_start < dist_to_end:
            # 连接头部：将找到的线段反转后加到前面
            points = list(reversed(points_to_prepend))
            print(f"步骤 {step + 1}: 连接到头部 {current_start} -> 新线段 {poly_to_prepend.id} (连接点: {points[-1]})")
            merged_points = points[:-1] + merged_points
            polylines_to_process.remove(poly_to_prepend)
        else:
            # 连接尾部：将找到的线段追加到后面
            print(
                f"步骤 {step + 1}: 连接到尾部 {current_end} -> 新线段 {poly_to_append.id} (连接点: {points_to_append[0]})")
            merged_points.extend(points_to_append[1:])
            polylines_to_process.remove(poly_to_append)

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


def plot_merge_verification(original_polylines, merged_polyline):
    """
    绘制原始多段线和合并后的结果以进行验证。

    参数:
        original_polylines (list): 用于合并的原始多段线列表。
        merged_polyline (Polyline): merge_polylines 函数返回的合并结果。
    """
    plt.figure(figsize=(12, 8))

    # 1. 绘制所有原始线段作为背景参考
    # 只为第一个线段添加标签，避免图例混乱
    has_labeled = False
    for polyline in original_polylines:
        if not polyline.points:
            continue
        x = [p.x for p in polyline.points]
        y = [p.y for p in polyline.points]
        if not has_labeled:
            plt.plot(x, y, color='gray', linestyle='--', linewidth=1.5, marker='.', label='Original Segments')
            has_labeled = True
        else:
            plt.plot(x, y, color='gray', linestyle='--', linewidth=1.5, marker='.')

    # 2. 绘制合并后的最终结果
    if merged_polyline and merged_polyline.points:
        x = [p.x for p in merged_polyline.points]
        y = [p.y for p in merged_polyline.points]

        # 使用醒目的颜色和样式突出显示合并结果
        plt.plot(x, y, color='red', linewidth=3, marker='o', markersize=5, label='Merged Result')

        # 标记最终的起点和终点
        plt.scatter(x[0], y[0], color='green', s=150, zorder=5, label='Final Start', marker='o', edgecolors='black')
        plt.scatter(x[-1], y[-1], color='blue', s=150, zorder=5, label='Final End', marker='s', edgecolors='black')

    # 3. 设置图表属性
    plt.title('Verification of Polyline Merging')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')  # 保持纵横比
    plt.show()