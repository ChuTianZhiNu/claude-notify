import json
import sys
import os

try:
    import requests  # noqa: F401
except ImportError:
    print("[feishu-notify] 缺少依赖，请运行: pip install requests", file=sys.stderr)
    sys.exit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feishu_client import load_config, FeishuClient


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

    client = FeishuClient(config)
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
