import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _mock_sys_exit():
    """返回一个 mock sys.exit，调用时抛出 SystemExit 以模拟真实行为。"""
    m = Mock(side_effect=SystemExit)
    return m


def test_main_stop_event():
    """Stop 事件应发送任务完成通知"""
    stdin_data = {
        "hook_event_name": "Stop",
        "cwd": "/Users/test/project",
        "last_assistant_message": "任务已完成",
        "stop_hook_active": False,
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.FeishuClient") as mock_client_cls, \
         patch("notify.WebhookClient") as mock_webhook_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "notify_type": "api",
            "app_id": "cli_test",
            "app_secret": "secret_test",
            "open_id": "ou_test",
            "notify_on_stop": True,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client.build_stop_card.return_value = {"msg_type": "interactive", "content": "{}"}
        mock_client_cls.return_value = mock_client
        from notify import main
        with pytest.raises(SystemExit):
            main("stop")
    mock_client.build_stop_card.assert_called_once()
    mock_client.send_message.assert_called_once()


def test_main_permission_event():
    """Permission 事件应发送权限审批通知"""
    stdin_data = {
        "hook_event_name": "Notification",
        "notification_type": "permission_prompt",
        "tool_name": "Bash",
        "tool_input": {"command": "npm install"},
        "cwd": "/Users/test/project",
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.FeishuClient") as mock_client_cls, \
         patch("notify.WebhookClient") as mock_webhook_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "notify_type": "api",
            "app_id": "cli_test",
            "app_secret": "secret_test",
            "open_id": "ou_test",
            "notify_on_stop": True,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client.build_permission_card.return_value = {"msg_type": "interactive", "content": "{}"}
        mock_client_cls.return_value = mock_client
        from notify import main
        with pytest.raises(SystemExit):
            main("permission")
    mock_client.build_permission_card.assert_called_once()
    mock_client.send_message.assert_called_once()


def test_main_notify_disabled():
    """通知开关关闭时不应发送消息"""
    stdin_data = {
        "hook_event_name": "Stop",
        "cwd": "/Users/test/project",
        "last_assistant_message": "任务已完成",
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.FeishuClient") as mock_client_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "app_id": "cli_test",
            "app_secret": "secret_test",
            "open_id": "ou_test",
            "notify_on_stop": False,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        from notify import main
        with pytest.raises(SystemExit):
            main("stop")
    mock_client_cls.assert_not_called()


def test_main_webhook_mode():
    """notify_type=webhook 时应使用 WebhookClient"""
    stdin_data = {
        "hook_event_name": "Stop",
        "cwd": "/test",
        "last_assistant_message": "done",
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.WebhookClient") as mock_webhook_cls, \
         patch("notify.FeishuClient") as mock_api_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "notify_type": "webhook",
            "webhook_url": "https://example.com/hook/xxx",
            "notify_on_stop": True,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client.build_stop_card.return_value = {"msg_type": "interactive", "content": "{}"}
        mock_webhook_cls.return_value = mock_client
        from notify import main
        with pytest.raises(SystemExit):
            main("stop")
    mock_webhook_cls.assert_called_once()
    mock_api_cls.assert_not_called()


def test_main_api_mode():
    """notify_type=api 时应使用 FeishuClient"""
    stdin_data = {
        "hook_event_name": "Stop",
        "cwd": "/test",
        "last_assistant_message": "done",
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.WebhookClient") as mock_webhook_cls, \
         patch("notify.FeishuClient") as mock_api_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "notify_type": "api",
            "app_id": "cli_test",
            "app_secret": "secret",
            "open_id": "ou_test",
            "notify_on_stop": True,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client.build_stop_card.return_value = {"msg_type": "interactive", "content": "{}"}
        mock_api_cls.return_value = mock_client
        from notify import main
        with pytest.raises(SystemExit):
            main("stop")
    mock_api_cls.assert_called_once()
    mock_webhook_cls.assert_not_called()


def test_main_missing_webhook_url():
    """webhook 模式缺少 webhook_url 时不应崩溃"""
    stdin_data = {
        "hook_event_name": "Stop",
        "cwd": "/test",
        "last_assistant_message": "done",
    }
    with patch("sys.stdin") as mock_stdin, \
         patch("notify.load_config") as mock_load, \
         patch("notify.WebhookClient") as mock_webhook_cls, \
         patch("notify.sys.exit", side_effect=SystemExit):
        mock_stdin.read.return_value = json.dumps(stdin_data)
        mock_config = {
            "notify_type": "webhook",
            "webhook_url": "",
            "notify_on_stop": True,
            "notify_on_permission": True,
            "max_summary_length": 200,
        }
        mock_load.return_value = mock_config
        from notify import main
        with pytest.raises(SystemExit):
            main("stop")
    mock_webhook_cls.assert_not_called()
