class ClosedShape:
    def __init__(self, intersections, work_line_1, work_line_2, tangent_line_1, tangent_line_2, polygon):
        self.intersections = intersections
        self.work_line_1 = work_line_1
        self.work_line_2 = work_line_2
        self.tangent_line_1 = tangent_line_1
        self.tangent_line_2 = tangent_line_2
        self.polygon = polygon

    def contains_point(self, point):
        return self.polygon.contains(point)

    def __repr__(self):
        return f"ClosedShape(intersections={self.intersections})"
