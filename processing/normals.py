
import numpy as np
from tqdm import tqdm
from shapely.geometry import LineString
from collections import defaultdict
from rtree import index

# 去除交叉法线的处理

def remove_crossing_normals(points_with_normals):
    """
    去除相交的法线，只保留不交叉的法线。(使用RTree优化过程)
    """
    n = len(points_with_normals)
    alive = [True] * n  # 标记法线是否存活

    #初始化RTree树
    idx = index.Index(properties=index.Property(dimension=2))
    for i in range(n):
        line = points_with_normals[i][1]
        idx.insert(i, line.bounds)

    # 初始化交叉次数和相交关系
    crossings = {}
    intersecting_pairs = {}

    # 初始统计交叉次数和相交关系
    for i in range(n):
        if not alive[i]:
            continue
        line1 = points_with_normals[i][1]
        cross_count = 0
        intersecting = set()

        candidates=list(idx.intersection(line1.bounds))

        for j in candidates:
            if i == j or not alive[j]:
                continue
            line2 = points_with_normals[j][1]
            if line1.intersects(line2):
                cross_count += 1
                intersecting.add(j)
        crossings[i] = cross_count
        intersecting_pairs[i] = intersecting

    # 计算初始交叉的法线数目
    crossing_lines = [i for i in crossings if crossings[i] > 0 and alive[i]]
    total_crossings = len(crossing_lines)

    pbar = tqdm(total=total_crossings, desc="Removing crossing normals", unit="line")
    previous_crossings = total_crossings

    while total_crossings > 0:
        # 找到当前交叉次数最多的存活法线
        candidates = [i for i in crossings if alive[i] and crossings[i] > 0]
        if not candidates:
            break
        max_cross_index = max(candidates, key=lambda x: crossings[x])

        # 移除该法线（标记为非存活）
        alive[max_cross_index] = False

        # 更新与该法线相交的其他法线的交叉次数
        for m in intersecting_pairs.get(max_cross_index, set()):
            if alive[m]:
                crossings[m] -= 1
                intersecting_pairs[m].discard(max_cross_index)

        # 从字典中移除被删除的法线记录
        del crossings[max_cross_index]
        del intersecting_pairs[max_cross_index]

        # 重新计算剩余交叉法线数目
        current_crossing = sum(1 for i in crossings if alive[i] and crossings[i] > 0)
        progress_increment = previous_crossings - current_crossing
        pbar.update(progress_increment)
        pbar.set_postfix({"Remaining": current_crossing})
        previous_crossings = current_crossing
        total_crossings = current_crossing

    pbar.set_postfix({"Final count": sum(alive)})
    pbar.close()

    # 收集存活的法线
    return [p for i, p in enumerate(points_with_normals) if alive[i]]

def generate_infinite_normals_on_linestring_with_polyline(line, north, south, interval=100):
    """
    生成多段线上的法线，使用 north 和 south 作为参考线来计算法线方向。

    :param line: 多段线 (LineString)。
    :param north: 北岸参考线 (LineString)，用于确定法线的方向。
    :param south: 南岸参考线 (LineString)，用于确定法线的方向。
    :param interval: 间隔距离（米），用于在多段线的每个点之间生成法线。
    :return: 返回包含法线的点与法线的元组列表。
    """
    line_length = line.length
    points_with_normals = []  # 用于存储每个点和对应的法线
    print(f"分割距离为{interval}")
    # 使用 tqdm 来创建进度条
    pbar = tqdm(range(0, int(line_length) + 1, interval), desc="Processing normals", unit="point")

    for distance in pbar:
        try:
            point = line.interpolate(distance)

            # 计算切线方向
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

            # 计算法线方向，垂直于切线
            normal_vector = np.array([-tangent_vector[1], tangent_vector[0]])
            normal_vector = normal_vector / np.linalg.norm(normal_vector)  # 单位化法线

            # 使用 north 和 south 线确定法线的最终方向
            if north.contains(point):  # 如果点在 north 线的北边
                normal_vector = -normal_vector  # 反转法线方向

            # 生成无限法线
            offset_start = np.array([point.x, point.y]) - (normal_vector * 1e6)
            offset_end = np.array([point.x, point.y]) + (normal_vector * 1e6)
            infinite_normal_line = LineString([offset_start, offset_end])

            # 计算法线与 north 和 south 的交点
            intersection_with_north = infinite_normal_line.intersection(north)
            intersection_with_south = infinite_normal_line.intersection(south)

            if intersection_with_north.is_empty and intersection_with_south.is_empty:
                continue

            north_points = []
            if not intersection_with_north.is_empty:
                if intersection_with_north.geom_type == 'MultiPoint':
                    north_points.extend(intersection_with_north.geoms)
                else:
                    north_points.append(intersection_with_north)

            south_points = []
            if not intersection_with_south.is_empty:
                if intersection_with_south.geom_type == 'MultiPoint':
                    south_points.extend(intersection_with_south.geoms)
                else:
                    south_points.append(intersection_with_south)

            north_point = min(north_points, key=lambda p: p.distance(point)) if north_points else None
            south_point = min(south_points, key=lambda p: p.distance(point)) if south_points else None

            if north_point and south_point:
                normal_line = LineString([north_point, south_point])
                points_with_normals.append((point, normal_line))
            else:
                continue

        except Exception as e:
            pbar.set_postfix({"Error": str(e)})
            continue

    pbar.set_postfix({"Processed": len(points_with_normals)})
    points_with_normals = remove_crossing_normals(points_with_normals)
    pbar.set_postfix({"Final count": len(points_with_normals)})

    return points_with_normals
