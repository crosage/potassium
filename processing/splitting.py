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
        subcurve = substring(line, distance1, distance2)

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

def preprocess_crop_lines(centerline, left_line, right_line):
    """
    裁剪三条线（中心线、北/左岸、南/右岸），使它们具有相同的空间范围。

    Args:
        centerline (LineString): 河道中心线。
        left_line (LineString): 北岸/左岸线。
        right_line (LineString): 南岸/右岸线。

    Returns:
        tuple: 一个包含三条裁剪后LineString的元组
               (cropped_centerline, cropped_left_line, cropped_right_line)。
               如果不存在有效的重叠区域，则返回 (None, None, None)。
    """
    print("--- 开始执行智能裁剪预处理 ---")

    # 1. 确定共同起点距离
    # 获取岸线起点的投影位置
    left_start_proj_dist = centerline.project(Point(left_line.coords[0]))
    right_start_proj_dist = centerline.project(Point(right_line.coords[0]))

    # 共同起点是所有起点中最“靠后”的那个
    common_start_dist = max(left_start_proj_dist, right_start_proj_dist)
    print(f"检测到共同起点位于中心线 {common_start_dist:.2f} 米处。")

    # 2. 确定共同终点距离
    # 获取岸线终点的投影位置
    left_end_proj_dist = centerline.project(Point(left_line.coords[-1]))
    right_end_proj_dist = centerline.project(Point(right_line.coords[-1]))

    # 共同终点是所有终点中最“靠前”的那个
    common_end_dist = min(centerline.length, left_end_proj_dist, right_end_proj_dist)
    print(f"检测到共同终点位于中心线 {common_end_dist:.2f} 米处。")

    # 3. 检查是否存在有效的重叠区域
    if common_start_dist >= common_end_dist:
        print("错误：三条线之间没有找到有效的重叠区域。")
        return None, None, None

    # 4. 执行裁剪
    print("正在裁剪所有线以匹配共同范围...")

    # 4.1 裁剪中心线 (最直接)
    start_point_on_center = centerline.interpolate(common_start_dist)
    end_point_on_center = centerline.interpolate(common_end_dist)
    cropped_centerline = extract_subcurve(centerline, start_point_on_center, end_point_on_center)

    # 4.2 裁剪北岸线
    # 找到裁剪后的中心线端点在北岸线上的对应投影点
    start_point_on_left = left_line.interpolate(left_line.project(start_point_on_center))
    end_point_on_left = left_line.interpolate(left_line.project(end_point_on_center))
    cropped_left_line = extract_subcurve(left_line, start_point_on_left, end_point_on_left)

    # 4.3 裁剪南岸线
    start_point_on_right = right_line.interpolate(right_line.project(start_point_on_center))
    end_point_on_right = right_line.interpolate(right_line.project(end_point_on_center))
    cropped_right_line = extract_subcurve(right_line, start_point_on_right, end_point_on_right)

    print("--- 裁剪完成 ---")

    return cropped_centerline, cropped_left_line, cropped_right_line
