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
        assert result == config_data
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
