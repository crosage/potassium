import os
import geopandas as gpd
import glob

def get_shp_crs_in_folder(folder_path):
    """
    读取指定文件夹内所有 SHP 文件的坐标参考系统 (CRS)。

    参数:
    folder_path (str): 包含 SHP 文件的文件夹路径。
    """
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在。")
        return

    print(f"正在扫描文件夹: {folder_path}\n")

    # 使用 glob 查找所有 .shp 后缀的文件
    # os.path.join 用于构建跨平台的兼容路径
    shp_files = glob.glob(os.path.join(folder_path, '*.shp'))

    if not shp_files:
        print("未在该文件夹下找到任何 SHP 文件。")
        return

    # 遍历找到的 SHP 文件列表
    for shp_path in shp_files:
        try:
            # 读取 shapefile
            gdf = gpd.read_file(shp_path)

            # 获取文件名
            filename = os.path.basename(shp_path)

            # 打印文件名和坐标系信息
            # gdf.crs 会返回一个 pyproj.CRS 对象
            if gdf.crs:
                print(f"文件: {filename}")
                print(f"  ├─ CRS 名称: {gdf.crs.name}")
                print(f"  └─ CRS 信息 (WKT): \n{gdf.crs.to_wkt(pretty=True)}\n")
            else:
                # 如果 shapefile 没有关联的 .prj 文件，则 crs 可能为 None
                print(f"文件: {filename}")
                print(f"  └─ CRS 信息: 未定义 (可能缺少 .prj 文件)\n")

        except Exception as e:
            filename = os.path.basename(shp_path)
            print(f"处理文件 {filename} 时出错: {e}\n")


if __name__ == "__main__":
    target_folder = "D:\code\polyline\data"
    get_shp_crs_in_folder(target_folder)