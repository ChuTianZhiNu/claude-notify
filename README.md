# Claude Code 飞书通知插件

[English](#english) | 中文

Claude Code 钩子插件，在任务完成或需要权限审批时通过飞书发送卡片通知。

## 功能特性

- **任务完成通知** — Claude Code 完成长时间任务后推送飞书通知
- **权限审批通知** — Claude Code 需要权限审批时即时推送
- **按执行时长过滤** — 短任务不发通知，避免频繁打扰
- **双通道支持** — 群机器人 Webhook / 个人消息 API
- **零阻塞** — 异步发送，不影响 Claude Code 主流程

## 快速开始

```bash
git clone https://github.com/ChuTianZhiNu/claude-notify.git
cd claude-notify
bash install.sh
```

安装脚本会自动：
1. 检查 Python 环境和依赖
2. 引导选择通知方式并填写凭证
3. 配置 Claude Code Hooks
4. 发送测试通知验证

### 前置要求

- Python 3（macOS 自带）
- 飞书群机器人 Webhook URL 或飞书自建应用凭证

## 通知方式

### 方式一：群机器人 Webhook（推荐）

配置最简单，只需一个 URL。

1. 打开飞书群 → **群设置** → **群机器人** → **添加机器人**
2. 选择 **自定义机器人**，复制 Webhook 地址
3. 安装时选择 Webhook 方式，粘贴地址即可

### 方式二：个人消息 API

直接发送个人私聊消息，无需群聊。

1. 在 [飞书开发者后台](https://open.feishu.cn/app) 创建自建应用
2. 开启 **机器人能力**
3. 添加权限 `im:message` 或 `im:message:send_as_bot`
4. 发布应用，可用范围选自己
5. 通过 API 调试工具获取你的 `open_id`

## 配置说明

安装完成后，编辑 `~/.claude/plugins/feishu-notify/config.json`：

```json
{
  "notify_type": "webhook",
  "webhook_url": "你的 Webhook 地址",
  "app_id": "",
  "app_secret": "",
  "open_id": "",
  "notify_on_stop": true,
  "notify_on_permission": true,
  "max_summary_length": 200,
  "min_task_duration": 60
}
```

| 字段 | 说明 | 默认值 |
|---|---|---|
| `notify_type` | 通知方式：`webhook` 或 `api` | `webhook` |
| `webhook_url` | 群机器人 Webhook 地址 | - |
| `app_id` | 飞书应用 ID（API 模式） | - |
| `app_secret` | 飞书应用密钥（API 模式） | - |
| `open_id` | 消息接收者 ID（API 模式） | - |
| `notify_on_stop` | 是否在任务完成时通知 | `true` |
| `notify_on_permission` | 是否在需要审批时通知 | `true` |
| `max_summary_length` | 任务摘要最大长度 | `200` |
| `min_task_duration` | 任务最短通知阈值（秒），低于此值不发通知 | `60` |

## 项目结构

```
claude-notify/
├── notify.py           # 入口脚本，解析 Hook 事件并分发通知
├── feishu_client.py    # 飞书 API 封装（Webhook / 个人消息）
├── config.json         # 用户配置
├── install.sh          # 一键安装脚本
└── tests/              # 测试
    ├── test_feishu_client.py
    └── test_notify.py
```

## 运行测试

```bash
cd ~/.claude/plugins/feishu-notify
python3 -m pytest tests/ -v
```

## 工作原理

```
用户发消息 → UserPromptSubmit Hook → 记录时间戳
                                          ↓
Claude 工作...                              ↓
                                          ↓
任务完成   → Stop Hook → 计算时长 → 超过阈值 → 飞书通知
需要审批   → Notification Hook → 即时 → 飞书通知
```

## 卸载

```bash
# 删除插件文件
rm -rf ~/.claude/plugins/feishu-notify

# 从 settings.json 中移除 hooks（需手动编辑）
# 删除 UserPromptSubmit、Stop、Notification 中 feishu-notify 相关的配置
```

## License

MIT

---

<a id="english"></a>

# Claude Code Feishu Notification Plugin

[中文](#claude-code-飞书通知插件) | English

A Claude Code hook plugin that sends Feishu (Lark) card notifications when tasks complete or permission approval is needed.

## Features

- **Task completion notification** — Push Feishu notification when Claude Code finishes long-running tasks
- **Permission approval notification** — Instant push when Claude Code requests permission
- **Duration-based filtering** — Suppress notifications for short tasks to reduce noise
- **Dual channel support** — Group bot Webhook / Personal message API
- **Non-blocking** — Async delivery, doesn't interrupt Claude Code workflow

## Quick Start

```bash
git clone https://github.com/ChuTianZhiNu/claude-notify.git
cd claude-notify
bash install.sh
```

The install script automatically:
1. Checks Python environment and dependencies
2. Guides you through notification setup and credential configuration
3. Configures Claude Code Hooks
4. Sends a test notification for verification

### Prerequisites

- Python 3 (pre-installed on macOS)
- Feishu group bot Webhook URL or Feishu app credentials

## Notification Methods

### Method 1: Group Bot Webhook (Recommended)

Simplest setup, only requires a URL.

1. Open a Feishu group → **Group Settings** → **Group Bots** → **Add Bot**
2. Select **Custom Bot**, copy the Webhook URL
3. Choose Webhook during installation and paste the URL

### Method 2: Personal Message API

Sends direct personal messages without needing a group.

1. Create a custom app at [Feishu Developer Console](https://open.feishu.cn/app)
2. Enable **Bot capability**
3. Add permission `im:message` or `im:message:send_as_bot`
4. Publish the app, set availability to yourself
5. Get your `open_id` via the API debugging tool

## Configuration

After installation, edit `~/.claude/plugins/feishu-notify/config.json`:

```json
{
  "notify_type": "webhook",
  "webhook_url": "your webhook url",
  "app_id": "",
  "app_secret": "",
  "open_id": "",
  "notify_on_stop": true,
  "notify_on_permission": true,
  "max_summary_length": 200,
  "min_task_duration": 60
}
```

| Field | Description | Default |
|---|---|---|
| `notify_type` | Notification method: `webhook` or `api` | `webhook` |
| `webhook_url` | Group bot Webhook URL | - |
| `app_id` | Feishu app ID (API mode) | - |
| `app_secret` | Feishu app secret (API mode) | - |
| `open_id` | Recipient ID (API mode) | - |
| `notify_on_stop` | Notify on task completion | `true` |
| `notify_on_permission` | Notify on permission request | `true` |
| `max_summary_length` | Max task summary length | `200` |
| `min_task_duration` | Minimum task duration in seconds to trigger notification | `60` |

## Project Structure

```
claude-notify/
├── notify.py           # Entry script, parses Hook events and dispatches notifications
├── feishu_client.py    # Feishu API wrapper (Webhook / Personal message)
├── config.json         # User configuration
├── install.sh          # One-click install script
└── tests/              # Tests
    ├── test_feishu_client.py
    └── test_notify.py
```

## Running Tests

```bash
cd ~/.claude/plugins/feishu-notify
python3 -m pytest tests/ -v
```

## How It Works

```
User sends message → UserPromptSubmit Hook → Record timestamp
                                                    ↓
Claude is working...                                ↓
                                                    ↓
Task done    → Stop Hook → Check duration → Exceeds threshold → Feishu notification
Needs approval → Notification Hook → Instant → Feishu notification
```

## Uninstall

```bash
# Remove plugin files
rm -rf ~/.claude/plugins/feishu-notify

# Remove hooks from settings.json (manual edit required)
# Delete feishu-notify related entries in UserPromptSubmit, Stop, and Notification hooks
```

## License

MIT
