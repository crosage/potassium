"""
该模块提供了多段线、法线、封闭形状等数据的可视化展示功能，支持在操作结束后使用 matplotlib 进行结果展示。
"""

import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon


def set_equal_aspect_ratio():
    """
    设置 Matplotlib 图表的横纵坐标比例为相等，避免出现拉伸。
    """
    plt.gca().set_aspect('equal', adjustable='box')


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
    plt.plot(x_north, y_north, marker='o', linestyle='-', color='g', label='North Line')

    # 绘制南线
    x_south, y_south = zip(*south_line.coords)
    plt.plot(x_south, y_south, marker='o', linestyle='-', color='b', label='South Line')

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_normals(normals, title="Normals Visualization"):
    """
    绘制法线。
    """
    if not normals:
        print("没有法线可展示。")
        return

    plt.figure(figsize=(12, 8))

    for point, normal in normals:
        plt.scatter(point.x, point.y, color='r', zorder=5)
        x, y = zip(*normal.coords)
        plt.plot(x, y, linestyle='--', color='k', alpha=0.7)

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True)
    plt.show()


def plot_closed_shapes(closed_shapes, title="Closed Shapes Visualization"):
    """
    绘制封闭形状。
    """
    if not closed_shapes:
        print("没有封闭形状可展示。")
        return

    plt.figure(figsize=(12, 8))

    for idx, shape in enumerate(closed_shapes):
        polygon = shape.polygon if hasattr(shape, 'polygon') else shape['polygon']
        x, y = polygon.exterior.xy
        plt.fill(x, y, alpha=0.4, label=f'Shape {idx + 1}')

    set_equal_aspect_ratio()
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.grid(True)
    plt.show()
