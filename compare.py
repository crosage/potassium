import pandas as pd
import numpy as np
import os


def build_reports(
        auto_csv_path: str,
        out_dir: str = "output",
):
    os.makedirs(out_dir, exist_ok=True)

    # 1) 读取 CSV
    df = pd.read_csv(auto_csv_path)

    # 2) 计算逐行误差
    df["error_m"] = df["堤坝线投影长度"] - df["人工投影长度"]
    df["abs_error_m"] = df["error_m"].abs()
    df["squared_error_m2"] = df["error_m"] ** 2

    # 使用 np.maximum 作为分母
    den = np.maximum(df["人工投影长度"], df["堤坝线投影长度"])

    df["绝对百分比误差(%)"] = (df["abs_error_m"] / den) * 100.0

    per_row = df.copy()

    # 3) 按 (CODE,RIVERPART) 聚合 (逻辑不变)
    def agg_block(g):
        mae = float(g["abs_error_m"].mean())
        rmse = float(np.sqrt(g["squared_error_m2"].mean()))
        mape_macro = float(g["绝对百分比误差(%)"].mean(skipna=True))

        return pd.Series({
            "name": g["name"].iloc[0],
            "records": len(g),
            "latest_date": pd.to_datetime(g["DATE"], errors="coerce").max(),
            "人工投影长度_mean": float(g["人工投影长度"].mean()),
            "堤坝线投影长度_mean": float(g["堤坝线投影长度"].mean()),
            "MAE_m": mae,
            "RMSE_m": rmse,
            "MAPE_percent_macro_per_ditch": mape_macro,
        })

    per_ditch = (
        per_row.groupby(["CODE", "RIVERPART"], as_index=False)
        .apply(agg_block)
        .reset_index(drop=True)
    )

    # --- 4) 全局指标 (MODIFIED) ---
    global_mse = float(per_row["squared_error_m2"].mean())
    global_rmse = float(np.sqrt(global_mse))

    # 直接使用已计算好的列来得到全局 Macro-MAPE，这保证了逻辑统一
    macro_mape_all = float(per_row["绝对百分比误差(%)"].mean(skipna=True))

    # 直接使用已计算好的列来得到全局 Micro-MAPE
    # Micro-MAPE = SUM(abs_errors) / SUM(denominators) * 100
    # 我们需要重新计算分母列，因为它在 per_row 中没有被单独保存
    micro_den_series = np.maximum(per_row["人工投影长度"], per_row["堤坝线投影长度"])
    # 同样要处理真实值和预测值都无效的情况
    mask = (per_row["人工投影长度"] > 0) & per_row["堤坝线投影长度"].notna()

    micro_num = per_row.loc[mask, "abs_error_m"].sum()
    micro_den = micro_den_series[mask].sum()
    micro_mape_all = (micro_num / micro_den) * 100.0 if micro_den > 0 else np.nan

    # 5) 导出 (逻辑不变)
    per_row_path = os.path.join(out_dir, "per_row_errors.csv")
    per_ditch_path = os.path.join(out_dir, "per_ditch_summary.csv")
    per_row.to_csv(per_row_path, index=False)
    per_ditch.to_csv(per_ditch_path, index=False)

    print(f"✔ 明细表: {per_row_path}")
    print(f"✔ 汇总表: {per_ditch_path}")
    print(
        f"Global (Algo vs Manual)  MSE:  {global_mse:.6f} (m^2), "
        f"RMSE: {global_rmse:.3f} m, Macro-MAPE: {macro_mape_all:.3f}%, "
        f"Micro-MAPE: {micro_mape_all:.3f}%"
    )

    return per_row, per_ditch, {
        "Algo_vs_Manual": {
            "MSE": global_mse,
            "RMSE": global_rmse,
            "MacroMAPE": macro_mape_all,
            "MicroMAPE": micro_mape_all
        }
    }
# 使用示例
if __name__ == "__main__":
    per_row_df, per_ditch_df, metrics = build_reports(
        # auto_csv_path="D:\code\polyline\output\ditch_origin\ditch_results.csv",
        # auto_csv_path="D:\code\polyline\output\ditch_origin\ditch_results.csv",
        auto_csv_path="D:\code\polyline\output\ditch_PAEK_SM2_1000\ditch_results.csv",
        out_dir="output\ditch_PAEK_SM2_1000"
    )
