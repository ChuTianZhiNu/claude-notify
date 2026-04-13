import json
import sys
import os
import requests

_FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
_FEISHU_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
_REQUEST_TIMEOUT = 5

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


class FeishuClient:
    def __init__(self, config):
        self.app_id = config["app_id"]
        self.app_secret = config["app_secret"]
        self.open_id = config["open_id"]
        self._token = None

    def get_access_token(self):
        """获取 tenant_access_token，带内存缓存。"""
        if self._token:
            return self._token
        try:
            resp = requests.post(
                _FEISHU_TOKEN_URL,
                json={"app_id": self.app_id, "app_secret": self.app_secret},
                timeout=_REQUEST_TIMEOUT,
            )
            data = resp.json()
            if data.get("code") == 0:
                self._token = data["tenant_access_token"]
                return self._token
            print(f"[feishu-notify] 获取 token 失败: {data.get('msg')}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[feishu-notify] 获取 token 异常: {e}", file=sys.stderr)
            return None
