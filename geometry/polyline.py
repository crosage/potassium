"""
多段线相关的几何计算、长度估计、点距计算以及平滑处理
"""
from shapely.geometry import LineString, Point
from scipy.interpolate import CubicSpline
import numpy as np
import time


class Polyline:
    def __init__(self, id, points):
        self.id = id
        self.points = points
        self.line = LineString(self.points)

    def __repr__(self):
        return f"Polyline(id={self.id}, points={self.points})"

    def length_between_points(self, point1, point2):
        point1 = Point(point1)
        point2 = Point(point2)
        projected_point1 = self.line.project(point1)
        projected_point2 = self.line.project(point2)

        if projected_point1 > projected_point2:
            projected_point1, projected_point2 = projected_point2, projected_point1

        subline = self.line.interpolate(projected_point1).coords[:] + self.line.interpolate(projected_point2).coords[:]
        subline = LineString(subline)

        return self.line.project(Point(subline.coords[0]), normalized=True) * self.line.length - self.line.project(
            Point(subline.coords[-1]), normalized=True) * self.line.length

    def distance_to_point(self, point):
        return point.distance(self.line)

    def estimate_length(self):
        total_length = 0.0
        for i in range(len(self.points) - 1):
            point1 = self.points[i]
            point2 = self.points[i + 1]
            distance = point1.distance(point2)
            total_length += distance

        return total_length

    def smooth_with_interval(self, segment_length=1000, new_id=None):
        if segment_length <= 0:
            raise ValueError("Segment length must be greater than 0.")

        start_time = time.time()
        total_distance = self.line.length
        num_segments = int(np.ceil(total_distance / segment_length))

        segment_start = 0
        refined_points = []
        processed_segments = 0

        for segment_index in range(num_segments):
            segment_process_start = time.time()
            segment_end = min(segment_start + segment_length, total_distance)

            segment_points = []
            for d in np.linspace(segment_start, segment_end, num=50):
                segment_points.append(self.line.interpolate(d))

            local_x = [point.x for point in segment_points]
            local_y = [point.y for point in segment_points]
            local_distances = np.linspace(0, segment_end - segment_start, len(local_x))

            cs_x = CubicSpline(local_distances, local_x, bc_type='natural')
            cs_y = CubicSpline(local_distances, local_y, bc_type='natural')

            smooth_distances = np.linspace(0, segment_end - segment_start, num=100)
            smooth_x = cs_x(smooth_distances)
            smooth_y = cs_y(smooth_distances)

            refined_points.extend(list(zip(smooth_x, smooth_y)))
            segment_start = segment_end
            processed_segments += 1

            segment_process_end = time.time()
            segment_time = segment_process_end - segment_process_start
            avg_time_per_segment = (segment_process_end - start_time) / processed_segments
            remaining_segments = num_segments - processed_segments
            eta = remaining_segments * avg_time_per_segment

            progress = (processed_segments / num_segments) * 100
            print(f"[Progress: {progress:.2f}%] Processed {processed_segments}/{num_segments} segments | "
                  f"Time per segment: {segment_time:.2f}s | ETA: {eta:.2f}s")

        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total smoothing time: {total_time:.2f} s")

        new_polyline = Polyline(
            id=new_id if new_id else self.id,
            points=refined_points
        )
        return new_polyline
