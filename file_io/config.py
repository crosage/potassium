import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

def load_config():
    """
    从配置文件加载配置，如果文件不存在，返回默认配置。
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        default_config = {
            "north_south_lines": "north_south_lines.json",
            "split_points": "split_points.json",
            "closed_shapes": "closed_shapes.json",
            "merged_polyline": "merged_polyline.json"
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"{CONFIG_FILE} not found. Created with default config.")
        return default_config

def save_config(config):
    """
    将配置保存到文件。
    """
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def update_path(key, path):
    """
    更新某个操作的路径配置。
    """
    config = load_config()
    config[key] = path
    save_config(config)
