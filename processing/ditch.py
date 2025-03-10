import csv
import hashlib
import math
import os
from matplotlib import pyplot as plt
from tqdm import tqdm
from processing.splitting import extract_subcurve
from utils.helpers import make_shape_finder


def process_ditch_endpoints(ditchs, closed_shapes,north_line,south_line, centerline, save_path=None, log=True):
    results = []
    print(f"{type(north_line)}   {type(south_line)}")
    finder=make_shape_finder(closed_shapes)
    csv_filename = "ditch_results.csv"  # 默认CSV文件名
    if save_path:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        csv_filename = os.path.join(save_path, "ditch_results.csv")

    with open(csv_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "清沟标号", "清沟实际长度", "南岸长度", "北岸长度", "中心线长度"
        ])

        for idx, ditch in tqdm(enumerate(ditchs), total=len(ditchs), desc="处理清沟", unit="个"):
            if len(ditch.points) < 2:
                print(f"⚠️ 警告：清沟 {ditch.id} 只有一个点，跳过。")
                continue

            start_point = ditch.points[0]
            end_point = ditch.points[-1]

            # 处理起点
            start_index, start_shape = finder(start_point)
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
            end_index, end_shape = finder(end_point)
            if end_shape:
                proj_end_1 = end_shape.tangent_line_1.project(end_point)
                proj_end_2 = end_shape.tangent_line_2.project(end_point)
                proj_end_1_point = end_shape.tangent_line_1.interpolate(proj_end_1)
                proj_end_2_point = end_shape.tangent_line_2.interpolate(proj_end_2)
            else:
                proj_end_1_point = None
                proj_end_2_point = None
                print(f"⚠️ 清沟 {ditch.id} 的终点不在任何 ClosedShape 中。")

            proj_start_centerline=centerline.line.project(start_point)
            proj_start_centerline_point=centerline.line.interpolate(proj_start_centerline)
            proj_end_centerline=centerline.line.project(end_point)
            proj_end_centerline_point=centerline.line.interpolate(proj_end_centerline)

            north_length=extract_subcurve(north_line,proj_start_1_point,proj_end_1_point).length
            south_length=extract_subcurve(south_line,proj_start_2_point,proj_end_2_point).length
            ditch_length=extract_subcurve(ditch.line,ditch.points[0],ditch.points[-1]).length
            centerline_length=extract_subcurve(centerline.line,proj_start_centerline_point,proj_end_centerline_point).length

            # print(f"ditch{idx}结果{ditch_length}")
            # 存储结果
            result_item = {
                "ditch_id": ditch.id,
                "ditch_length": ditch_length,
                "south_length": south_length,
                "north_length": north_length,
                "centerline_length": centerline_length,
            }
            results.append(result_item)

            csv_writer.writerow([
                ditch.id,
                f"{ditch_length:.2f}",
                f"{south_length:.2f}",
                f"{north_length:.2f}",
                f"{centerline_length:.2f}",
            ])


            # 绘制清沟和其他元素
            if log:
                fig, ax = plt.subplots(figsize=(12, 8))

                # 绘制中心线
                x, y = centerline.line.xy
                ax.plot(x, y, color="gray", linewidth=2)

                # 绘制清沟
                x = [point.x for point in ditch.points]
                y = [point.y for point in ditch.points]
                ax.plot(x, y, label=f"Ditch {ditch.id}", color="blue", linewidth=2)
                sqr=math.sqrt((end_point.x - start_point.x) ** 2 + (end_point.y - start_point.y) ** 2)
                # 绘制文本，展示南北长度，调整字体样式和颜色
                ax.text(0.6, 0.2, f"North Length: {north_length:.2f} meters", color='#4e3629', fontsize=14,
                        fontweight='light', fontname='sans-serif', transform=ax.transAxes, ha='center', va='center')
                ax.text(0.6, 0.1, f"South Length: {south_length:.2f} meters", color='#4e3629', fontsize=14,
                        fontweight='light', fontname='sans-serif', transform=ax.transAxes, ha='center', va='center')
                ax.text(0.6, 0.3, f"ditch: {ditch_length:.2f} meters", color='#4e3629', fontsize=14,
                        fontweight='light', fontname='sans-serif', transform=ax.transAxes, ha='center', va='center')
                ax.text(0.6, 0.4, f"centerline: {centerline_length:.2f} meters", color='#4e3629', fontsize=14,
                        fontweight='light', fontname='sans-serif', transform=ax.transAxes, ha='center', va='center')

                ax.scatter(start_point.x, start_point.y, color='red', label='Start Point', zorder=5)
                ax.scatter(end_point.x, end_point.y, color='purple', label='End Point', zorder=5)

                #起点投影点
                if proj_start_1_point:
                    ax.scatter(proj_start_1_point.x, proj_start_1_point.y, color='orange', zorder=5, s=10)
                    ax.plot([start_point.x, proj_start_1_point.x], [start_point.y, proj_start_1_point.y], color='orange',
                            linestyle='--')
                if proj_start_2_point:
                    ax.scatter(proj_start_2_point.x, proj_start_2_point.y, color='cyan', zorder=5, s=10)
                    ax.plot([start_point.x, proj_start_2_point.x], [start_point.y, proj_start_2_point.y], color='cyan',
                            linestyle='--')

                #终点投影点
                if proj_end_1_point:
                    ax.scatter(proj_end_1_point.x, proj_end_1_point.y, color='orange', zorder=5, s=10)
                    ax.plot([end_point.x, proj_end_1_point.x], [end_point.y, proj_end_1_point.y], color='orange',
                            linestyle='--')
                if proj_end_2_point:
                    ax.scatter(proj_end_2_point.x, proj_end_2_point.y, color='cyan', zorder=5, s=10)
                    ax.plot([end_point.x, proj_end_2_point.x], [end_point.y, proj_end_2_point.y], color='cyan',
                            linestyle='--')

                # 绘制起点和终点的投影线
                if proj_start_centerline_point:
                    ax.scatter(proj_start_centerline_point.x, proj_start_centerline_point.y, color='lime', zorder=5, s=30)
                    ax.plot([start_point.x, proj_start_centerline_point.x], [start_point.y, proj_start_centerline_point.y], color='lime', linestyle='--', linewidth=2)

                if proj_end_centerline_point:
                    ax.scatter(proj_end_centerline_point.x, proj_end_centerline_point.y, color='lime', zorder=5, s=30)
                    ax.plot([end_point.x, proj_end_centerline_point.x], [end_point.y, proj_end_centerline_point.y], color='lime', linestyle='--', linewidth=2)


                # 绘制封闭形状
                for j, shape in enumerate(closed_shapes):
                    hash_input = str(j).encode('utf-8')
                    hash_digest = hashlib.md5(hash_input).hexdigest()
                    color = '#' + hash_digest[:6]

                    px, py = shape.polygon.exterior.xy
                    ax.fill(px, py, color=color, alpha=0.5)
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

                # 保存或展示图像
                if save_path:
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)

                    plt.savefig(f"{save_path}/ditch_{ditch.id}_projections.png", dpi=100, bbox_inches='tight')
                    plt.close()
                else:
                    plt.show()

    return results