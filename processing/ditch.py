import hashlib
import os
from matplotlib import pyplot as plt
from tqdm import tqdm
from utils.helpers import find_point_in_closed_shapes


def process_ditch_endpoints(ditchs, closed_shapes, centerline, save_path=None, log=True):
    results = []

    for idx, ditch in tqdm(enumerate(ditchs), total=len(ditchs), desc="处理清沟", unit="个"):
        if len(ditch.points) < 2:
            print(f"⚠️ 警告：清沟 {ditch.id} 只有一个点，跳过。")
            continue

        start_point = ditch.points[0]
        end_point = ditch.points[-1]

        # 处理起点
        start_index, start_shape = find_point_in_closed_shapes(start_point, closed_shapes)
        if start_shape:
            proj_start_1 = start_shape.tangent_line_1.project(start_point)
            proj_start_2 = start_shape.tangent_line_2.project(start_point)
            proj_start_1_point = start_shape.tangent_line_1.interpolate(proj_start_1)
            proj_start_2_point = start_shape.tangent_line_2.interpolate(proj_start_2)
        else:
            proj_start_1_point = None
            proj_start_2_point = None
            print(f"⚠️ 清沟 {ditch.id} 的起点不在任何 ClosedShape 中。")

        # 处理终点
        end_index, end_shape = find_point_in_closed_shapes(end_point, closed_shapes)
        if end_shape:
            proj_end_1 = end_shape.tangent_line_1.project(end_point)
            proj_end_2 = end_shape.tangent_line_2.project(end_point)
            proj_end_1_point = end_shape.tangent_line_1.interpolate(proj_end_1)
            proj_end_2_point = end_shape.tangent_line_2.interpolate(proj_end_2)
        else:
            proj_end_1_point = None
            proj_end_2_point = None
            print(f"⚠️ 清沟 {ditch.id} 的终点不在任何 ClosedShape 中。")

        # 存储结果
        results.append({
            "ditch_id": ditch.id,
            "start_point": (start_point.x, start_point.y),
            "start_proj_tangent_1": (proj_start_1_point.x, proj_start_1_point.y) if proj_start_1_point else None,
            "start_proj_tangent_2": (proj_start_2_point.x, proj_start_2_point.y) if proj_start_2_point else None,
            "end_point": (end_point.x, end_point.y),
            "end_proj_tangent_1": (proj_end_1_point.x, proj_end_1_point.y) if proj_end_1_point else None,
            "end_proj_tangent_2": (proj_end_2_point.x, proj_end_2_point.y) if proj_end_2_point else None,
        })

        if log:
            fig, ax = plt.subplots(figsize=(12, 8))

            x, y = centerline.line.xy
            ax.plot(x, y, color="gray", linewidth=2)
            # 绘制清沟
            x = [point.x for point in ditch.points]
            y = [point.y for point in ditch.points]
            ax.plot(x, y, label=f"Ditch {ditch.id}", color="blue", linewidth=2)

            # 绘制端点
            ax.scatter(start_point.x, start_point.y, color='red', label='Start Point', zorder=5)
            ax.scatter(end_point.x, end_point.y, color='purple', label='End Point', zorder=5)

            # 绘制起点投影点
            if proj_start_1_point:
                ax.scatter(proj_start_1_point.x, proj_start_1_point.y, color='orange', zorder=5, s=10)
                ax.plot([start_point.x, proj_start_1_point.x], [start_point.y, proj_start_1_point.y], color='orange',
                        linestyle='--')
            if proj_start_2_point:
                ax.scatter(proj_start_2_point.x, proj_start_2_point.y, color='cyan', zorder=5, s=10)
                ax.plot([start_point.x, proj_start_2_point.x], [start_point.y, proj_start_2_point.y], color='cyan',
                        linestyle='--')

            # 绘制终点投影点
            if proj_end_1_point:
                ax.scatter(proj_end_1_point.x, proj_end_1_point.y, color='orange', zorder=5, s=10)
                ax.plot([end_point.x, proj_end_1_point.x], [end_point.y, proj_end_1_point.y], color='orange',
                        linestyle='--')
            if proj_end_2_point:
                ax.scatter(proj_end_2_point.x, proj_end_2_point.y, color='cyan', zorder=5, s=10)
                ax.plot([end_point.x, proj_end_2_point.x], [end_point.y, proj_end_2_point.y], color='cyan',
                        linestyle='--')

            for j, shape in enumerate(closed_shapes):
                hash_input = str(j).encode('utf-8')
                hash_digest = hashlib.md5(hash_input).hexdigest()
                color = '#' + hash_digest[:6]

                px, py = shape.polygon.exterior.xy
                ax.fill(px, py, color=color, alpha=0.5, label=f"Closed Shape {j}" if j == 0 else "")
                ax.plot(px, py, color="red", linewidth=0.7)

            # 设置展示范围：清沟周围上下左右 1000 米
            min_x = min(x)
            max_x = max(x)
            min_y = min(y)
            max_y = max(y)

            ax.set_xlim(min_x - 5000, max_x + 5000)
            ax.set_ylim(min_y - 5000, max_y + 5000)

            ax.set_title(f"Ditch {ditch.id} with Projections")
            ax.set_xlabel("X Coordinate")
            ax.set_ylabel("Y Coordinate")
            ax.legend()
            ax.set_aspect('equal', adjustable='box')
            plt.grid(True)

            if save_path:
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                    # print(f"文件夹 {save_path} 已创建。")

                plt.savefig(f"{save_path}/ditch_{ditch.id}_projections.png", dpi=300, bbox_inches='tight')
                # print(f"图像已保存到 {save_path}/ditch_{ditch.id}_projections.png")
                plt.close()
            else:
                plt.show()
    return results
