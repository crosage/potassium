import csv

def calculate_error_and_output_csv(csv_file_path, output_csv_path):
    """
    读取CSV文件，计算估值误差和百分比误差，并将结果输出到CSV文件。
    平均值也参与最接近的计算，并计算所有误差的平均值，以及误差百分比的平均值。

    Args:
        csv_file_path (str): 输入CSV文件路径。
        output_csv_path (str): 输出CSV文件路径。
    """
    average_average_error_sum = 0
    average_closest_error_sum = 0
    average_average_error_percentage_sum = 0  # 新增：平均误差百分比累加器
    average_closest_error_percentage_sum = 0  # 新增：最接近误差百分比累加器
    row_count = 0

    with open(csv_file_path, 'r', encoding='gbk') as infile, open(output_csv_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # 读取表头并写入输出CSV文件
        header = next(reader)
        output_header = [
            header[0],  # 清沟标号
            header[1],  # 清沟实际长度
            'Average Estimate',     # 平均估值
            'Average Error',        # 平均误差
            'Average Error (%)',    # 平均误差百分比
            'Closest Estimate (Avg Included)', # 最接近估值 (包含平均值)
            'Closest Error (Avg Included)',     # 最接近误差 (包含平均值)
            'Closest Error (%) (Avg Included)'  # 最接近误差百分比 (包含平均值)
        ]
        writer.writerow(output_header)

        next(reader) # 跳过第二行，也就是中文标题行

        for row_number, row in enumerate(reader, start=2):
            try:
                clearing_mark_no = row[0]
                actual_length = float(row[1])
                south_bank_length = float(row[2])
                north_bank_length = float(row[3])
                center_line_length = float(row[4])
                average_estimate = (south_bank_length + north_bank_length + center_line_length) / 3
                average_error = abs(actual_length - average_estimate)
                average_error_percentage = (average_error / actual_length) * 100 if actual_length != 0 else 0
                all_estimates = [south_bank_length, north_bank_length, center_line_length, average_estimate] #  包含平均值
                error_list = [abs(actual_length - val) for val in all_estimates]
                closest_error_avg_included = min(error_list)
                closest_index_avg_included = error_list.index(closest_error_avg_included)
                closest_estimate_avg_included = all_estimates[closest_index_avg_included]
                closest_error_percentage_avg_included = (closest_error_avg_included / actual_length) * 100 if actual_length != 0 else 0

                average_average_error_sum += average_error
                average_closest_error_sum += closest_error_avg_included
                average_average_error_percentage_sum += average_error_percentage # 累加平均误差百分比
                average_closest_error_percentage_sum += closest_error_percentage_avg_included # 累加最接近误差百分比
                row_count += 1
                output_row = [
                    clearing_mark_no,
                    f"{actual_length:.2f}",
                    f"{average_estimate:.2f}",
                    f"{average_error:.2f}",
                    f"{average_error_percentage:.2f}%",
                    f"{closest_estimate_avg_included:.2f}",
                    f"{closest_error_avg_included:.2f}",
                    f"{closest_error_percentage_avg_included:.2f}%"
                ]
                writer.writerow(output_row)

            except ValueError as e:
                print(f"Error converting data in row {row_number}: {e}, Data row: {row}")
            except IndexError as e:
                print(f"Index error in row {row_number}: {e}, Data row: {row}")

    final_average_average_error = average_average_error_sum / row_count if row_count > 0 else 0
    final_average_closest_error = average_closest_error_sum / row_count if row_count > 0 else 0
    final_average_average_error_percentage = average_average_error_percentage_sum / row_count if row_count > 0 else 0 # 计算平均平均误差百分比
    final_average_closest_error_percentage = average_closest_error_percentage_sum / row_count if row_count > 0 else 0 # 计算平均最接近误差百分比

    # writer.writerow([]) # 空行分隔数据和平均值  (您可以选择是否取消注释这些行，将平均值写入 CSV)
    # writer.writerow(['Average Errors', ''])
    # writer.writerow(['Average of Average Error', f"{final_average_average_error:.2f}"])
    # writer.writerow(['Average of Closest Error (Avg Included)', f"{final_average_closest_error:.2f}"])
    # writer.writerow(['Average of Average Error Percentage', f"{final_average_average_error_percentage:.2f}%"]) #  写入平均平均误差百分比
    # writer.writerow(['Average of Closest Error Percentage (Avg Included)', f"{final_average_closest_error_percentage:.2f}%"]) # 写入平均最接近误差百分比


    print(f"结果已输出到文件: {output_csv_path}")
    print(f"所有行的平均 '平均误差': {final_average_average_error:.2f}")
    print(f"所有行的平均 '最接近误差 (包含平均值)': {final_average_closest_error:.2f}")
    print(f"所有行的平均 '平均误差百分比': {final_average_average_error_percentage:.2f}%") # 输出平均平均误差百分比
    print(f"所有行的平均 '最接近误差百分比 (包含平均值)': {final_average_closest_error_percentage:.2f}%") # 输出平均最接近误差百分比


# 设置CSV文件路径
input_csv_file_path = r'D:\code\polyline\output\ditch_origin\ditch_results.csv' # 您的输入CSV文件路径, 使用 raw string 防止反斜杠问题
output_csv_file_path = r'D:\code\polyline\output\ditch_origin\ditch_test_results.csv' # 输出CSV文件路径, 使用 raw string
calculate_error_and_output_csv(input_csv_file_path, output_csv_file_path)