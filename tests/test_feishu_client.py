import json
import os
import tempfile
import pytest
from unittest.mock import Mock, patch


def test_load_config_missing_file():
    """config.json 不存在时应返回 None 并打印警告"""
    from feishu_client import load_config
    with patch("sys.stderr"):
        result = load_config("/nonexistent/path/config.json")
    assert result is None


def test_load_config_invalid_json():
    """config.json 格式错误时应返回 None"""
    from feishu_client import load_config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{invalid json")
        path = f.name
    try:
        with patch("sys.stderr"):
            result = load_config(path)
        assert result is None
    finally:
        os.unlink(path)


def test_load_config_valid():
    """正确格式的 config.json 应正常解析"""
    from feishu_client import load_config
    config_data = {
        "app_id": "cli_test",
        "app_secret": "secret_test",
        "open_id": "ou_test",
        "notify_on_stop": True,
        "notify_on_permission": True,
        "max_summary_length": 200
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        path = f.name
    try:
        result = load_config(path)
        # load_config 会自动填充默认值（如 notify_type）
        assert result["app_id"] == config_data["app_id"]
        assert result["app_secret"] == config_data["app_secret"]
        assert result["open_id"] == config_data["open_id"]
        assert result["notify_on_stop"] is True
        assert result["notify_on_permission"] is True
        assert result["max_summary_length"] == 200
        assert result["notify_type"] == "webhook"  # 默认值
    finally:
        os.unlink(path)


def test_load_config_defaults():
    """缺少可选字段时使用默认值"""
    from feishu_client import load_config
    config_data = {
        "app_id": "cli_test",
        "app_secret": "secret_test",
        "open_id": "ou_test"
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        path = f.name
    try:
        result = load_config(path)
        assert result["notify_on_stop"] is True
        assert result["notify_on_permission"] is True
        assert result["max_summary_length"] == 200
    finally:
        os.unlink(path)


def test_get_tenant_access_token_success():
    """成功获取 token 应缓存并返回"""
    from feishu_client import FeishuClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 0,
        "tenant_access_token": "t-test-token",
        "expire": 7200
    }
    with patch("feishu_client.requests.post", return_value=mock_response) as mock_post:
        client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
        token = client.get_access_token()
    assert token == "t-test-token"
    assert mock_post.call_count == 1


def test_get_tenant_access_token_cached():
    """token 已缓存时不应重复请求"""
    from feishu_client import FeishuClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 0,
        "tenant_access_token": "t-test-token",
        "expire": 7200
    }
    with patch("feishu_client.requests.post", return_value=mock_response):
        client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
        token1 = client.get_access_token()
        token2 = client.get_access_token()
    assert token1 == token2


def test_get_tenant_access_token_retry():
    """API 返回错误码时应返回 None"""
    from feishu_client import FeishuClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 9999,
        "msg": "invalid app_id"
    }
    with patch("feishu_client.requests.post", return_value=mock_response):
        client = FeishuClient({"app_id": "cli_bad", "app_secret": "bad", "open_id": "ou_test"})
        token = client.get_access_token()
    assert token is None


def test_build_stop_card_success():
    """任务完成的成功卡片应包含正确字段"""
    from feishu_client import FeishuClient
    client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
    card = client.build_stop_card(
        cwd="/Users/test/project",
        status="success",
        summary="已完成认证模块重构",
        max_length=200,
    )
    assert card["msg_type"] == "interactive"
    content = json.loads(card["content"])
    elements = content["elements"]
    full_text = json.dumps(elements, ensure_ascii=False)
    assert "✅" in full_text
    assert "/Users/test/project" in full_text
    assert "已完成认证模块重构" in full_text


def test_build_stop_card_truncated_summary():
    """摘要超长时应该被截断"""
    from feishu_client import FeishuClient
    client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
    long_summary = "x" * 500
    card = client.build_stop_card(
        cwd="/Users/test/project",
        status="success",
        summary=long_summary,
        max_length=100,
    )
    content = json.loads(card["content"])
    full_text = json.dumps(content)
    assert "..." in full_text


def test_build_permission_card():
    """权限审批卡片应包含工具名和输入参数"""
    from feishu_client import FeishuClient
    client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
    card = client.build_permission_card(
        cwd="/Users/test/project",
        tool_name="Bash",
        tool_input={"command": "rm -rf /tmp/test"},
    )
    assert card["msg_type"] == "interactive"
    content = json.loads(card["content"])
    full_text = json.dumps(content, ensure_ascii=False)
    assert "⚠️" in full_text
    assert "Bash" in full_text
    assert "rm -rf /tmp/test" in full_text


def test_send_message_success():
    """成功发送消息应返回 True"""
    from feishu_client import FeishuClient
    mock_token_resp = Mock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"code": 0, "tenant_access_token": "t-test", "expire": 7200}
    mock_send_resp = Mock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {"code": 0, "msg": "success"}
    with patch("feishu_client.requests.post") as mock_post:
        mock_post.side_effect = [mock_token_resp, mock_send_resp]
        client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
        result = client.send_message({"msg_type": "text", "content": '{"text":"hi"}'})
    assert result is True


def test_send_message_api_error():
    """飞书 API 返回错误时应重试一次，仍失败返回 False"""
    from feishu_client import FeishuClient
    mock_token_resp = Mock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"code": 0, "tenant_access_token": "t-test", "expire": 7200}
    mock_send_resp = Mock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {"code": 9999, "msg": "error"}
    with patch("feishu_client.requests.post") as mock_post:
        mock_post.side_effect = [mock_token_resp, mock_send_resp, mock_token_resp, mock_send_resp]
        client = FeishuClient({"app_id": "cli_test", "app_secret": "secret_test", "open_id": "ou_test"})
        result = client.send_message({"msg_type": "text", "content": '{"text":"hi"}'})
    assert result is False


def test_webhook_client_send_success():
    """Webhook 发送成功应返回 True"""
    from feishu_client import WebhookClient
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"code": 0, "msg": "success"}
    with patch("feishu_client.requests.post", return_value=mock_resp) as mock_post:
        client = WebhookClient({"webhook_url": "https://example.com/hook/xxx"})
        result = client.send_message({"msg_type": "interactive", "content": "{}"})
    assert result is True
    mock_post.assert_called_once()


def test_webhook_client_send_failure():
    """Webhook 发送失败应返回 False"""
    from feishu_client import WebhookClient
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"code": 9999, "msg": "error"}
    with patch("feishu_client.requests.post", return_value=mock_resp):
        client = WebhookClient({"webhook_url": "https://example.com/hook/xxx"})
        result = client.send_message({"msg_type": "interactive", "content": "{}"})
    assert result is False


def test_webhook_client_build_stop_card():
    """WebhookClient 的 build_stop_card 应与 FeishuClient 一致"""
    from feishu_client import WebhookClient
    client = WebhookClient({"webhook_url": "https://example.com/hook/xxx"})
    card = client.build_stop_card(cwd="/test", status="success", summary="done")
    assert card["msg_type"] == "interactive"


def test_webhook_client_build_permission_card():
    """WebhookClient 的 build_permission_card 应与 FeishuClient 一致"""
    from feishu_client import WebhookClient
    client = WebhookClient({"webhook_url": "https://example.com/hook/xxx"})
    card = client.build_permission_card(cwd="/test", tool_name="Bash", tool_input={"command": "ls"})
    assert card["msg_type"] == "interactive"
