"""
该模块提供了多段线、法线、封闭形状等数据的可视化展示功能，支持在操作结束后使用 matplotlib 进行结果展示。
"""
import hashlib

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

def plot_normals(normals, north_line, south_line, center_line):
    fig, ax = plt.subplots(figsize=(10, 8)) # Set figure size
    x_center, y_center = center_line.xy
    ax.plot(x_center, y_center, color='gray', linewidth=2, label='Centerline')

    x_north, y_north = north_line.xy
    ax.plot(x_north, y_north, color='red', label='North Line')
    x_south, y_south = south_line.xy
    ax.plot(x_south, y_south, color='green', label='South Line')
    if normals and isinstance(normals[0], tuple) and len(normals[0]) == 2 and isinstance(normals[0][0], Point) and isinstance(normals[0][1], LineString):
        for idx, (normal_point, normal_line) in enumerate(normals):
            x_normal, y_normal = normal_line.xy
            ax.plot(x_normal, y_normal, color='purple', linewidth=0.5, label='Normals' if idx == 0 else "_nolegend_") # Plot normal lines
            ax.scatter(normal_point.x, normal_point.y, marker='o', color='blue', s=10, label='Normal Points on Centerline' if idx == 0 else "_nolegend_") # Plot points on centerline where normals are generated
    else:
        print("Warning: Normals data format might not be as expected. Please check the data.")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_title("Normals and Boundary Lines", fontsize=16, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True)
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.show()

def plot_closed_shapes(closed_shapes, north_line, south_line, center_line):

    fig, ax = plt.subplots(figsize=(12, 8))

    x_center, y_center = center_line.xy
    ax.plot(x_center, y_center, color="gray", linewidth=2, label="Centerline")

    x_north, y_north = north_line.xy
    ax.plot(x_north, y_north, color='red', linestyle='--', label='North Boundary Line')
    x_south, y_south = south_line.xy
    ax.plot(x_south, y_south, color='green', linestyle='--', label='South Boundary Line')

    for j, shape in enumerate(closed_shapes):
        hash_input = str(j).encode('utf-8')
        hash_digest = hashlib.md5(hash_input).hexdigest()
        color = '#' + hash_digest[:6]

        px, py = shape.polygon.exterior.xy
        ax.fill(px, py, color=color, alpha=0.5, label='Closed Shapes' if j == 0 else "_nolegend_")
        ax.plot(px, py, color="red", linewidth=0.7)


    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_title("Closed Shapes Visualization", fontsize=16, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.show()
