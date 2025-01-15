"""
多段线分割为南岸和北岸
"""

from shapely.geometry import LineString, Point
from shapely.ops import substring
import matplotlib.pyplot as plt


def extract_subcurve(line, point1, point2, log=False):
    """
    从 LineString 中提取从 point1 到 point2 的子曲线。
    """
    try:
        distance1 = line.project(point1)
        distance2 = line.project(point2)

        print(f"Point1 在折线上的距离: {distance1}")
        print(f"Point2 在折线上的距离: {distance2}")

        subcurve = substring(line, distance1, distance2)
        print(f"提取的子曲线长度: {subcurve.length}")

        if log:
            plot_subcurve(line, point1, point2, subcurve)

        return subcurve

    except Exception as e:
        print(f"提取子曲线时发生错误: {e}")
        return LineString()


def split_polyline_by_points(work_polyline, point1, point2, point1_index, point2_index, log=False):
    """
    根据给定的两个点，将多段线切割为两部分。(南北两部分)
    """
    try:
        coords = list(work_polyline.coords)
        start_index = point1_index
        end_index = point2_index

        if start_index < end_index:
            north_coords = coords[start_index:end_index + 1]
            south_coords = coords[end_index:] + coords[:start_index + 1]
        else:
            north_coords = coords[start_index:] + coords[:end_index + 1]
            south_coords = [coord for coord in coords if coord not in north_coords]

        north_line = LineString(north_coords)
        south_line = LineString(south_coords)

        if log:
            plot_split_polyline(work_polyline, point1, point2, north_line, south_line)

        return north_line, south_line

    except Exception as e:
        print(f"切割多段线时发生错误: {e}")
        return LineString(), LineString()


def plot_subcurve(line, point1, point2, subcurve):
    """
    可视化子曲线提取过程，仅在 log=True 时启用。
    """
    plt.figure(figsize=(10, 6))

    # 绘制原始多段线
    x, y = line.xy
    plt.plot(x, y, label='Original Line', color='blue')

    # 绘制子曲线
    sub_x, sub_y = subcurve.xy
    plt.plot(sub_x, sub_y, label='Subcurve', color='green', linewidth=2)

    plt.scatter(point1.x, point1.y, color='red', label='Point 1', zorder=5)
    plt.scatter(point2.x, point2.y, color='orange', label='Point 2', zorder=5)

    plt.title('Extracted Subcurve')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_split_polyline(work_polyline, point1, point2, north_line, south_line):
    """
    可视化多段线分割过程，仅在 log=True 时启用。
    """
    plt.figure(figsize=(12, 8))

    x, y = work_polyline.xy
    plt.plot(x, y, label="Original Polyline", color="blue", linewidth=2)

    x_north, y_north = north_line.xy
    plt.plot(x_north, y_north, label="North Line", color="green", linewidth=2)

    x_south, y_south = south_line.xy
    plt.plot(x_south, y_south, label="South Line", color="orange", linewidth=2)

    plt.scatter(point1.x, point1.y, color="red", label="Point 1", zorder=5)
    plt.scatter(point2.x, point2.y, color="purple", label="Point 2", zorder=5)

    plt.title('Polyline Splitting')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()
