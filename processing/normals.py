
import numpy as np
from shapely.geometry import LineString
from tqdm import tqdm


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

    # 去除交叉法线的处理
    def remove_crossing_normals(points_with_normals):
        """
        去除相交的法线，只保留不交叉的法线。
        """
        # 初始时统计交叉法线的数量
        crossings = {}
        for i, (_, line1) in enumerate(points_with_normals):
            crossings[i] = 0
            for j, (_, line2) in enumerate(points_with_normals):
                if i != j and line1.intersects(line2):
                    crossings[i] += 1

        # 计算总共交叉的法线数
        crossing_lines = [index for index, count in crossings.items() if count > 0]
        total_crossings = len(crossing_lines)

        # 初始化进度条，total 设置为交叉法线的数量
        pbar = tqdm(total=total_crossings, desc="Removing crossing normals", unit="line")

        previous_crossings = total_crossings  # 初始化前一个交叉法线数

        while total_crossings > 0:
            try:
                # 找到交点最多的法线并移除
                max_cross_index = max(crossings, key=crossings.get)
                max_cross_count = crossings[max_cross_index]

                if max_cross_count == 0:
                    break  # 没有交叉的法线，跳出循环

                # 移除交叉的法线
                points_with_normals.pop(max_cross_index)

                # 重新计算交叉法线数量
                crossings = {}
                for i, (_, line1) in enumerate(points_with_normals):
                    crossings[i] = 0
                    for j, (_, line2) in enumerate(points_with_normals):
                        if i != j and line1.intersects(line2):
                            crossings[i] += 1

                # 重新计算交叉法线数目
                crossing_lines = [index for index, count in crossings.items() if count > 0]
                total_crossings = len(crossing_lines)

                # 计算进度条的增量
                progress_increment = previous_crossings - total_crossings
                previous_crossings = total_crossings  # 更新为当前交叉法线数

                # 更新进度条
                pbar.set_postfix({"Remaining": total_crossings})
                pbar.update(progress_increment)  # 根据交叉法线数的变化更新进度条

            except Exception as e:
                print(f"Error removing crossing normal: {e}")
                break

        pbar.set_postfix({"Final count": len(points_with_normals)})
        pbar.close()  # 关闭进度条

        return points_with_normals

    points_with_normals = remove_crossing_normals(points_with_normals)
    pbar.set_postfix({"Final count": len(points_with_normals)})

    return points_with_normals
