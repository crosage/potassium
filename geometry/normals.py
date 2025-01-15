from shapely.geometry import LineString, Point, MultiPoint
import numpy as np
from tqdm import tqdm
import time


def generate_infinite_normals_on_linestring_with_polyline(line, north, south, interval=100):
    line_length = line.length
    num_intervals = int(line_length) // interval + 1
    points_with_normals = []

    start_time = time.time()

    with tqdm(total=num_intervals, desc="生成法线") as pbar:
        for i, distance in enumerate(range(0, int(line_length) + 1, interval)):
            try:
                point = line.interpolate(distance)

                if distance == 0:
                    next_point = line.interpolate(distance + 1)
                    tangent_vector = np.array([next_point.x - point.x, next_point.y - point.y])
                elif distance >= line_length:
                    prev_point = line.interpolate(distance - 1)
                    tangent_vector = np.array([point.x - prev_point.x, point.y - prev_point.y])
                else:
                    prev_point = line.interpolate(distance - 1)
                    next_point = line.interpolate(distance + 1)
                    tangent_vector = np.array([next_point.x - prev_point.x, next_point.y - prev_point.y])

                normal_vector = np.array([-tangent_vector[1], tangent_vector[0]])
                normal_vector = normal_vector / np.linalg.norm(normal_vector)

                if north.contains(point):
                    normal_vector = -normal_vector

                offset_start = np.array([point.x, point.y]) - (normal_vector * 1e6)
                offset_end = np.array([point.x, point.y]) + (normal_vector * 1e6)
                infinite_normal_line = LineString([offset_start, offset_end])

                intersection_with_north = infinite_normal_line.intersection(north)
                intersection_with_south = infinite_normal_line.intersection(south)

                north_points = []
                if not intersection_with_north.is_empty:
                    if isinstance(intersection_with_north, MultiPoint):
                        north_points.extend(intersection_with_north.geoms)
                    else:
                        north_points.append(intersection_with_north)

                south_points = []
                if not intersection_with_south.is_empty:
                    if isinstance(intersection_with_south, MultiPoint):
                        south_points.extend(intersection_with_south.geoms)
                    else:
                        south_points.append(intersection_with_south)

                north_point = min(north_points, key=lambda p: p.distance(point)) if north_points else None
                south_point = min(south_points, key=lambda p: p.distance(point)) if south_points else None

                if north_point and south_point:
                    normal_line = LineString([north_point, south_point])
                    points_with_normals.append((point, normal_line))

            except Exception as e:
                print(f"在距离 {distance} 处发生异常: {e}")
                continue

            # 更新进度条
            pbar.update(1)
            elapsed_time = time.time() - start_time
            eta = elapsed_time / (i + 1) * (num_intervals - (i + 1))
            pbar.set_postfix(ETA=f"{eta:.2f}s")

    points_with_normals = remove_crossing_normals(points_with_normals)
    return points_with_normals


def remove_crossing_normals(points_with_normals):
    while True:
        try:
            crossings = {}
            total_lines = len(points_with_normals)
            start_time = time.time()

            # 初始化进度条
            with tqdm(total=total_lines, desc="Removing Crossing Normals") as pbar:
                for i, (_, line1) in enumerate(points_with_normals):
                    crossings[i] = 0
                    for j, (_, line2) in enumerate(points_with_normals):
                        if i != j and line1.intersects(line2):
                            crossings[i] += 1

                    pbar.update(1)
                    elapsed_time = time.time() - start_time
                    eta = elapsed_time / (i + 1) * (total_lines - (i + 1))
                    pbar.set_postfix(ETA=f"{eta:.2f}s")

            max_cross_index = max(crossings, key=crossings.get)
            max_cross_count = crossings[max_cross_index]

            if max_cross_count == 0:
                break

            points_with_normals.pop(max_cross_index)

        except Exception as e:
            print(f"在去除交叉法线时发生异常: {e}")
            break

    return points_with_normals

