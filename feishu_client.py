import json
import sys
import os
import requests
from datetime import datetime

_FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
_FEISHU_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
_REQUEST_TIMEOUT = 5

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULTS = {
    "notify_type": "webhook",
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


def build_stop_card(cwd, status, summary, max_length=200):
    """构建任务完成通知卡片。"""
    if status == "success":
        status_tag = "✅ 任务完成"
    else:
        status_tag = "❌ 任务失败"
    if summary and len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements = [
        {"tag": "markdown", "content": f"**{status_tag}**"},
        {"tag": "hr"},
        {"tag": "markdown", "content": f"📁 **项目:** `{cwd}`"},
    ]
    if summary:
        elements.append({"tag": "markdown", "content": f"📝 **摘要:** {summary}"})
    elements.append({"tag": "hr"})
    elements.append({"tag": "markdown", "content": f"🕐 {now}"})
    card = {
        "header": {"title": {"tag": "plain_text", "content": "Claude Code 通知"}},
        "elements": elements,
    }
    return {
        "msg_type": "interactive",
        "content": json.dumps(card),
    }


def build_permission_card(cwd, tool_name, tool_input):
    """构建权限审批通知卡片。"""
    input_str = json.dumps(tool_input, ensure_ascii=False, indent=2) if tool_input else "无"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements = [
        {"tag": "markdown", "content": "**⚠️ 需要权限审批**"},
        {"tag": "hr"},
        {"tag": "markdown", "content": f"📁 **项目:** `{cwd}`"},
        {"tag": "markdown", "content": f"🔧 **工具:** `{tool_name}`"},
        {"tag": "hr"},
        {"tag": "markdown", "content": f"📋 **请求内容:**\n```\n{input_str}\n```"},
        {"tag": "hr"},
        {"tag": "markdown", "content": f"🕐 {now}"},
    ]
    card = {
        "header": {"title": {"tag": "plain_text", "content": "Claude Code 权限审批"}},
        "elements": elements,
    }
    return {
        "msg_type": "interactive",
        "content": json.dumps(card),
    }


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

    def build_stop_card(self, cwd, status, summary, max_length=200):
        """构建任务完成通知卡片。"""
        return build_stop_card(cwd, status, summary, max_length)

    def build_permission_card(self, cwd, tool_name, tool_input):
        """构建权限审批通知卡片。"""
        return build_permission_card(cwd, tool_name, tool_input)

    def send_message(self, message_body):
        """发送消息到飞书，失败自动重试一次（清除 token 缓存）。"""
        token = self.get_access_token()
        if not token:
            return False
        try:
            resp = requests.post(
                _FEISHU_MSG_URL,
                params={"receive_id_type": "open_id"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "receive_id": self.open_id,
                    **message_body,
                },
                timeout=_REQUEST_TIMEOUT,
            )
            data = resp.json()
            if data.get("code") == 0:
                return True
            print(f"[feishu-notify] 发送消息失败: {data.get('msg')}", file=sys.stderr)
            # 清除 token 缓存重试一次
            self._token = None
            token = self.get_access_token()
            if not token:
                return False
            resp = requests.post(
                _FEISHU_MSG_URL,
                params={"receive_id_type": "open_id"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "receive_id": self.open_id,
                    **message_body,
                },
                timeout=_REQUEST_TIMEOUT,
            )
            data = resp.json()
            return data.get("code") == 0
        except Exception as e:
            print(f"[feishu-notify] 发送消息异常: {e}", file=sys.stderr)
            return False


class WebhookClient:
    def __init__(self, config):
        self.webhook_url = config["webhook_url"]

    def get_access_token(self):
        return True  # Webhook 不需要 token

    def build_stop_card(self, cwd, status, summary, max_length=200):
        """构建任务完成通知卡片。"""
        return build_stop_card(cwd, status, summary, max_length)

    def build_permission_card(self, cwd, tool_name, tool_input):
        """构建权限审批通知卡片。"""
        return build_permission_card(cwd, tool_name, tool_input)

    def send_message(self, message_body):
        """通过 Webhook 发送消息。"""
        try:
            resp = requests.post(
                self.webhook_url,
                json=message_body,
                timeout=_REQUEST_TIMEOUT,
            )
            data = resp.json()
            if data.get("code") == 0:
                return True
            print(f"[feishu-notify] Webhook 发送失败: {data.get('msg')}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[feishu-notify] Webhook 发送异常: {e}", file=sys.stderr)
            return False
