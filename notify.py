import json
import sys
import os

try:
    import requests  # noqa: F401
except ImportError:
    print("[feishu-notify] 缺少依赖，请运行: pip install requests", file=sys.stderr)
    sys.exit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feishu_client import load_config, FeishuClient, WebhookClient


def create_client(config):
    """根据 notify_type 创建对应的客户端实例。"""
    notify_type = config.get("notify_type", "webhook")
    if notify_type == "webhook":
        if not config.get("webhook_url"):
            print("[feishu-notify] 未配置 webhook_url", file=sys.stderr)
            return None
        return WebhookClient(config)
    elif notify_type == "api":
        if not config.get("app_id") or not config.get("app_secret") or not config.get("open_id"):
            print("[feishu-notify] 未配置 app_id/app_secret/open_id", file=sys.stderr)
            return None
        return FeishuClient(config)
    else:
        print(f"[feishu-notify] 不支持的 notify_type: {notify_type}", file=sys.stderr)
        return None


def main(event_type):
    """Claude Code Hook 入口。"""
    config = load_config()
    if not config:
        sys.exit(0)

    # 检查开关
    if event_type == "stop" and not config.get("notify_on_stop", True):
        sys.exit(0)
    if event_type == "permission" and not config.get("notify_on_permission", True):
        sys.exit(0)

    # 读取 stdin JSON
    try:
        raw = sys.stdin.read()
        context = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    client = create_client(config)
    if not client:
        sys.exit(0)
    cwd = context.get("cwd", "unknown")
    max_length = config.get("max_summary_length", 200)

    if event_type == "stop":
        summary = context.get("last_assistant_message", "")
        if context.get("stop_hook_active"):
            sys.exit(0)
        card = client.build_stop_card(cwd=cwd, status="success", summary=summary, max_length=max_length)
        client.send_message(card)
    elif event_type == "permission":
        tool_name = context.get("tool_name", "Unknown")
        tool_input = context.get("tool_input", {})
        card = client.build_permission_card(cwd=cwd, tool_name=tool_name, tool_input=tool_input)
        client.send_message(card)

    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("stop", "permission"):
        print("[feishu-notify] 用法: notify.py <stop|permission>", file=sys.stderr)
        sys.exit(0)
    main(sys.argv[1])
