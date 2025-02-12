import typer
from config import update_path

app = typer.Typer()

def set_north_south_lines_path(
        path: str = typer.Option(..., '-p', '--path', help="北岸与南岸线的保存路径")
):
    """
    设置北岸与南岸线的保存路径。
    """
    update_path("north_south_lines", path)
    print(f"Updated north-south lines path to: {path}")


def set_split_points_path(
        path: str = typer.Option(..., '-p', '--path', help="分割点的保存路径")
):
    """
    设置分割点的保存路径。
    """
    update_path("split_points", path)
    print(f"Updated split points path to: {path}")


def set_closed_shapes_path(
        path: str = typer.Option(..., '-p', '--path', help="封闭形状的保存路径")
):
    """
    设置封闭形状的保存路径。
    """
    update_path("closed_shapes", path)
    print(f"Updated closed shapes path to: {path}")


def set_merged_polyline_path(
        path: str = typer.Option(..., '-p', '--path', help="合并后的多段线的保存路径")
):
    """
    设置合并后的多段线的保存路径。
    """
    update_path("merged_polyline", path)
    print(f"Updated merged polyline path to: {path}")