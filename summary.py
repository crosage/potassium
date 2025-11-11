import os
import pandas as pd
import numpy as np


def process_ditch_results(csv_path, job_name):
    """
    处理单个ditch_results.csv文件，提取汇总统计信息
    """
    if not os.path.exists(csv_path):
        print(f"⚠ 文件不存在: {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)

        # 计算误差（如果CSV中没有这些列）
        if 'error_m' not in df.columns:
            df['error_m'] = df['堤坝线投影长度'] - df['人工投影长度']
        if 'abs_error_m' not in df.columns:
            df['abs_error_m'] = df['error_m'].abs()

        # 总长度统计
        total_manual_length = df['人工投影长度'].sum()
        total_algo_length = df['堤坝线投影长度'].sum()
        total_error = total_algo_length - total_manual_length
        total_percent_error = (abs(total_error) / total_manual_length * 100) if total_manual_length > 0 else np.nan

        # 按误差范围分类统计
        total_count = len(df)
        count_below_500 = len(df[df['abs_error_m'] < 500])
        count_500_1000 = len(df[(df['abs_error_m'] >= 500) & (df['abs_error_m'] < 1000)])
        count_above_1000 = len(df[df['abs_error_m'] >= 1000])

        ratio_below_500 = (count_below_500 / total_count * 100) if total_count > 0 else 0
        ratio_500_1000 = (count_500_1000 / total_count * 100) if total_count > 0 else 0
        ratio_above_1000 = (count_above_1000 / total_count * 100) if total_count > 0 else 0

        return {
            '日期': job_name,
            '单条清沟差异<500m占比(%)': ratio_below_500,
            '单条清沟差异500-1000m占比(%)': ratio_500_1000,
            '单条清沟差异>1000m占比(%)': ratio_above_1000,
            '算法计算总长度(m)': total_algo_length,
            '人工清沟总长度(m)': total_manual_length,
            '总长度误差(m)': total_error,
            '总体百分比误差(%)': total_percent_error,
            '清沟总数': total_count
        }

    except Exception as e:
        print(f"❌ 处理文件 {csv_path} 时出错: {e}")
        return None


def generate_summary_csv(output_dir="output", output_csv="清沟统计汇总.csv"):
    """
    遍历output目录下所有ditch_{job_name}文件夹，读取ditch_results.csv并生成汇总统计
    """
    print("\n--- 开始生成清沟统计汇总 ---")

    records = []

    # 遍历output目录
    for folder_name in sorted(os.listdir(output_dir)):
        if folder_name.startswith("ditch_"):
            job_name = folder_name.replace("ditch_", "")
            csv_path = os.path.join(output_dir, folder_name, "ditch_results.csv")

            print(f"处理任务: {job_name}")
            result = process_ditch_results(csv_path, job_name)

            if result:
                records.append(result)

    if not records:
        print("❌ 未找到任何ditch_results.csv文件")
        return

    # 创建DataFrame并按日期排序
    df = pd.DataFrame(records)
    df = df.sort_values(by='日期')

    # 保存CSV
    output_path = os.path.join(output_dir, output_csv)
    df.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.2f')

    print(f"\n✅ 汇总统计已保存至: {output_path}")
    print(f"共处理 {len(records)} 个任务")

    # 打印汇总统计
    print("\n" + "=" * 60)
    print("整体统计信息")
    print("=" * 60)
    print(f"总体人工清沟长度: {df['人工清沟总长度(m)'].sum():,.2f} m")
    print(f"总体算法计算长度: {df['算法计算总长度(m)'].sum():,.2f} m")
    print(f"总体误差: {df['总长度误差(m)'].sum():,.2f} m")

    total_manual = df['人工清沟总长度(m)'].sum()
    total_algo = df['算法计算总长度(m)'].sum()
    overall_error = abs(total_algo - total_manual) / total_manual * 100 if total_manual > 0 else np.nan
    print(f"总体百分比误差: {overall_error:.2f}%")

    print(f"\n清沟总数: {df['清沟总数'].sum()}")
    print(f"\n平均单条清沟差异<500m占比: {df['单条清沟差异<500m占比(%)'].mean():.2f}%")
    print(f"平均单条清沟差异500-1000m占比: {df['单条清沟差异500-1000m占比(%)'].mean():.2f}%")
    print(f"平均单条清沟差异>1000m占比: {df['单条清沟差异>1000m占比(%)'].mean():.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    generate_summary_csv("output", "清沟统计汇总.csv")