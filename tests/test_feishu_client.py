import json
import os
import tempfile
import pytest
from unittest.mock import patch


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
