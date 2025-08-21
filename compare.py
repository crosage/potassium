import pandas as pd
import geopandas as gpd
from collections import Counter
import numpy as np
import os

# ========== 工具函数 ==========
def load_manual_lengths(
    manual_shp_path: str,
    code_field: str = "CODE",
    part_field: str = "RIVERPART",
    target_crs: str = "EPSG:32650"
) -> pd.DataFrame:
    """读取人工投影 shp，并按 (CODE,RIVERPART) 汇总总长度（米）"""
    mgdf = gpd.read_file(manual_shp_path)
    if mgdf.crs is None or mgdf.crs.to_string() != target_crs:
        mgdf = mgdf.to_crs(target_crs)
    mgdf["manual_length_m"] = mgdf.geometry.length
    mgdf["_CODE"] = mgdf[code_field].astype(str)
    mgdf["_RIVERPART"] = mgdf[part_field].astype(str)
    manual_len = (
        mgdf.groupby(["_CODE", "_RIVERPART"], as_index=False)["manual_length_m"]
            .sum()
            .rename(columns={"_CODE": "CODE", "_RIVERPART": "RIVERPART"})
    )
    return manual_len

def pick_auto_truth(row) -> pd.Series:
    """从南/北/中心线投影长度中挑选与清沟实际长度最接近者作为自动真值"""
    actual = row.get("清沟实际长度")
    cand_cols = ["南岸投影长度", "北岸投影长度", "中心线投影长度"]
    cands = {col: row[col] for col in cand_cols if col in row and pd.notna(row[col])}
    if not cands or pd.isna(actual):
        return pd.Series({"auto_selected": pd.NA, "auto_from": pd.NA})
    chosen_col = min(cands.keys(), key=lambda c: abs(cands[c] - actual))
    return pd.Series({"auto_selected": cands[chosen_col], "auto_from": chosen_col})

def summarize_choice_counts(series):
    c = Counter(series.dropna())
    return {
        "picked_south_cnt": int(c.get("南岸投影长度", 0)),
        "picked_north_cnt": int(c.get("北岸投影长度", 0)),
        "picked_center_cnt": int(c.get("中心线投影长度", 0)),
    }

def macro_mape(y_true, y_pred):
    """Macro-MAPE：先逐条算 APE 再平均"""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = (y_true != 0) & np.isfinite(y_true) & np.isfinite(y_pred)
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_pred[mask] - y_true[mask]) / y_true[mask]) * 100.0))

def micro_mape(y_true, y_pred):
    """Micro-MAPE：∑|误差| / ∑真值 ×100%"""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = (y_true > 0) & np.isfinite(y_true) & np.isfinite(y_pred)
    num = float(np.sum(np.abs(y_pred[mask] - y_true[mask])))
    den = float(np.sum(y_true[mask]))
    return np.nan if den == 0 else (num / den) * 100.0

# ========== 主函数 ==========
def build_reports(
    auto_csv_path: str,
    manual_shp_path: str,
    out_dir: str = "output",
    code_field_auto: str = "编码",
    part_field_auto: str = "河流部分",
    code_field_manual: str = "CODE",
    part_field_manual: str = "RIVERPART",
    target_crs: str = "EPSG:32650",
    aggregate_global_rmse_by: str = "rows",  # 目前仍按逐行聚合，不使用该参数
):
    os.makedirs(out_dir, exist_ok=True)

    # 1) 自动结果
    df = pd.read_csv(auto_csv_path)

    # 键列（容错常见别名）
    def _pick_col(d, prefer, alts):
        if prefer in d.columns: return prefer
        for c in alts:
            if c in d.columns: return c
        raise KeyError(f"CSV 缺少列：{prefer} 或候选 {alts}")

    code_col = _pick_col(df, code_field_auto, ["编码", "CODE", "code", "编码(CODE)"])
    part_col = _pick_col(df, part_field_auto, ["河流部分", "RIVERPART", "riverpart", "河流部分(RIVERPART)"])

    df["CODE"] = df[code_col].astype(str)
    df["RIVERPART"] = df[part_col].astype(str)

    # 日期列（可选）
    date_col = next((c for c in ["日期", "DATE", "date", "Date"] if c in df.columns), None)
    df["__DATE_PARSED__"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT

    # 2) 自动真值选择（仍用“清沟实际长度”挑选最接近的一个，但不做任何对比指标）
    picked = df.apply(pick_auto_truth, axis=1)
    df = pd.concat([df, picked], axis=1)

    # 3) 人工长度合并
    manual_len = load_manual_lengths(
        manual_shp_path,
        code_field=code_field_manual,
        part_field=part_field_manual,
        target_crs=target_crs
    )
    merged = df.merge(
        manual_len,
        how="inner",
        on=["CODE", "RIVERPART"],
        validate="m:1"
    )

    # 4) 逐行误差（算法 vs 人工）
    merged["error_m"] = merged["auto_selected"] - merged["manual_length_m"]
    merged["abs_error_m"] = merged["error_m"].abs()
    merged["squared_error_m2"] = merged["error_m"] ** 2

    # APE%（算法 vs 人工，人工为 0 时置 NaN）
    den_manual = merged["manual_length_m"].replace(0, np.nan).abs()
    merged["APE_percent"] = (merged["abs_error_m"] / den_manual) * 100.0

    # 5) 明细表（仅保留算法 vs 人工）
    cols_internal = []
    if name_col := ("清沟名称(name)" if "清沟名称(name)" in merged.columns else ("清沟名称" if "清沟名称" in merged.columns else None)):
        cols_internal.append(name_col)
    if date_col: cols_internal.append(date_col)
    if "__DATE_PARSED__" in merged.columns:
        cols_internal.append("__DATE_PARSED__")
    cols_internal += [
        "CODE", "RIVERPART",
        "南岸投影长度", "北岸投影长度", "中心线投影长度",
        "auto_from", "auto_selected",
        # 可留存“清沟实际长度”列供查看，但不再参与任何误差计算
        "清沟实际长度" if "清沟实际长度" in merged.columns else None,
        "manual_length_m",
        "error_m", "abs_error_m", "squared_error_m2", "APE_percent",
    ]
    cols_internal = [c for c in cols_internal if c in merged.columns]
    per_row = merged[cols_internal].copy()

    # 对外列名映射
    rename_map = {
        "auto_from": "选择自",
        "auto_selected": "算法计算长度",
        "manual_length_m": "人工测算长度",
        "error_m": "误差长度",              # 算法 vs 人工（长度差）
        "APE_percent": "绝对百分比误差(%)",   # 算法 vs 人工（APE）
    }
    per_row = per_row.rename(columns=rename_map)

    # 列顺序（保留“清沟实际长度”但只是展示）
    desired_order = []
    if name_col and name_col in per_row.columns: desired_order.append(name_col)
    if date_col and date_col in per_row.columns: desired_order.append(date_col)
    desired_order += [
        "CODE", "RIVERPART",
        "南岸投影长度", "北岸投影长度", "中心线投影长度",
        "选择自", "算法计算长度",
        "清沟实际长度" if "清沟实际长度" in per_row.columns else None,
        "人工测算长度",
        "误差长度", "abs_error_m", "squared_error_m2", "绝对百分比误差(%)",
    ]
    per_row = per_row[[c for c in desired_order if c in per_row.columns]]

    # 6) 每清沟汇总（仅算法 vs 人工）
    def agg_block(g):
        mae = float(g["abs_error_m"].mean())
        rmse = float(np.sqrt(g["squared_error_m2"].mean()))
        mape_macro = float(g["绝对百分比误差(%)"].mean(skipna=True))

        choice_stats = summarize_choice_counts(g["选择自"])
        name_val = g[name_col].dropna().iloc[0] if name_col and g[name_col].notna().any() else pd.NA

        # 取最新日期（容错）
        if "__DATE_PARSED__" in g.columns:
            latest_date = g["__DATE_PARSED__"].max()
        elif ("日期" in g.columns):
            latest_date = pd.to_datetime(g["日期"], errors="coerce").max()
        else:
            latest_date = pd.NaT

        return pd.Series({
            "清沟名称": name_val,
            "records": len(g),
            "latest_date": latest_date,
            "人工测算长度_mean": float(g["人工测算长度"].mean()),
            "算法计算长度_mean": float(g["算法计算长度"].mean()),
            "MAE_m": mae,
            "RMSE_m": rmse,
            "MAPE_percent_macro_per_ditch": mape_macro,
            **choice_stats
        })

    per_ditch = (
        per_row.groupby(["CODE", "RIVERPART"], as_index=False)
               .apply(agg_block)
               .reset_index(drop=True)
    )

    # 7) 全局指标（仅算法 vs 人工）
    global_mse = float(merged["squared_error_m2"].mean())
    global_rmse = float(np.sqrt(global_mse))
    macro_mape_all = macro_mape(merged["manual_length_m"], merged["auto_selected"])
    micro_mape_all = micro_mape(merged["manual_length_m"], merged["auto_selected"])

    # 8) 导出
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


# ========== 使用示例 ==========
if __name__ == "__main__":
    per_row_df, per_ditch_df, metrics = build_reports(
        auto_csv_path="output/ditch_PEAKSM2_5000/ditch_results.csv",
        manual_shp_path="data/清沟映射汇总_2024-2025年度20250122.shp",
        out_dir="output",
        code_field_auto="编码",
        part_field_auto="河流部分",
        code_field_manual="CODE",
        part_field_manual="RIVERPART",
        target_crs="EPSG:32650",
        aggregate_global_rmse_by="rows"   # 或 "ditches"
    )
