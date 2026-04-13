import json
import sys
import os
import time

try:
    import requests  # noqa: F401
except ImportError:
    print("[feishu-notify] 缺少依赖，请运行: pip install requests", file=sys.stderr)
    sys.exit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feishu_client import load_config, FeishuClient, WebhookClient, TIMESTAMPS_DIR


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


def record_timestamp(session_id):
    """记录用户发消息的时间戳。"""
    os.makedirs(TIMESTAMPS_DIR, exist_ok=True)
    ts_file = os.path.join(TIMESTAMPS_DIR, f"{session_id}.ts")
    with open(ts_file, "w") as f:
        f.write(str(time.time()))


def get_task_duration(session_id):
    """读取上次记录的时间戳，返回经过的秒数。"""
    ts_file = os.path.join(TIMESTAMPS_DIR, f"{session_id}.ts")
    if not os.path.exists(ts_file):
        return None
    try:
        with open(ts_file, "r") as f:
            start_time = float(f.read().strip())
        return time.time() - start_time
    except (ValueError, OSError):
        return None


def main(event_type):
    """Claude Code Hook 入口。"""
    config = load_config()
    if not config:
        sys.exit(0)

    # 读取 stdin JSON
    try:
        raw = sys.stdin.read()
        context = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    session_id = context.get("session_id", "default")

    # record: 记录用户发消息的时间戳
    if event_type == "record":
        record_timestamp(session_id)
        sys.exit(0)

    # 检查开关
    if event_type == "stop" and not config.get("notify_on_stop", True):
        sys.exit(0)
    if event_type == "permission" and not config.get("notify_on_permission", True):
        sys.exit(0)

    client = create_client(config)
    if not client:
        sys.exit(0)

    cwd = context.get("cwd", "unknown")
    max_length = config.get("max_summary_length", 200)

    if event_type == "stop":
        if context.get("stop_hook_active"):
            sys.exit(0)

        # 检查任务执行时长，短任务跳过通知
        min_duration = config.get("min_task_duration", 60)
        duration = get_task_duration(session_id)
        if duration is not None and duration < min_duration:
            sys.exit(0)

        summary = context.get("last_assistant_message", "")
        # 在摘要中附加执行时长
        if duration is not None:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            summary = f"[耗时 {minutes}分{seconds}秒] {summary}"

        card = client.build_stop_card(cwd=cwd, status="success", summary=summary, max_length=max_length)
        client.send_message(card)
    elif event_type == "permission":
        tool_name = context.get("tool_name", "Unknown")
        tool_input = context.get("tool_input", {})
        card = client.build_permission_card(cwd=cwd, tool_name=tool_name, tool_input=tool_input)
        client.send_message(card)

    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("stop", "permission", "record"):
        print("[feishu-notify] 用法: notify.py <stop|permission|record>", file=sys.stderr)
        sys.exit(0)
    main(sys.argv[1])
