import json
import sys
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULTS = {
    "notify_on_stop": True,
    "notify_on_permission": True,
    "max_summary_length": 200,
}


def load_config(path=None):
    """加载配置文件，缺失可选字段时使用默认值。"""
    config_path = path or CONFIG_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[feishu-notify] 配置加载失败: {e}", file=sys.stderr)
        return None
    for key, value in DEFAULTS.items():
        config.setdefault(key, value)
    return config
