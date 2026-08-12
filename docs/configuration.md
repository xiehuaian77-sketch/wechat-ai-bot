# 配置说明

本文档介绍 WeChat AI Bot 的所有配置选项。

---

## 📋 配置方式

### 1. 环境变量（推荐）

```bash
# .env 文件
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ENABLE_WHITELIST=true
WHITELIST_USERS=wxid_123,wxid_456
```

### 2. 配置文件

```yaml
# config/config.yaml
app:
  name: WeChat AI Bot
  version: 0.1.0

llm:
  default_provider: openai
  providers:
    - openai
    - deepseek
    - anthropic

rag:
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
```

### 3. 命令行参数

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔑 环境变量

### 必需配置

| 变量名 | 说明 | 示例 | 必填 |
|--------|------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` | 否* |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | `sk-...` | 否* |
| `ANTHROPIC_API_KEY` | Claude API Key | `sk-ant-...` | 否* |

*至少配置其中一个

### 可选配置

#### 应用配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `APP_NAME` | 应用名称 | `WeChat AI Bot` | - |
| `APP_VERSION` | 应用版本 | `0.1.0` | - |
| `DEBUG` | 调试模式 | `false` | 开发环境 `true` |
| `LOG_LEVEL` | 日志级别 | `INFO` | 生产环境 `INFO` |
| `HOST` | 监听地址 | `0.0.0.0` | - |
| `PORT` | 监听端口 | `8000` | - |
| `WORKERS` | Worker 数量 | `4` | CPU 核心数 |

#### 微信配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `WECHAT_HOOK_URL` | ComWeChatRobot Hook URL | `http://localhost:8080/hook/wechat` | - |
| `WECHAT_TIMEOUT` | 微信消息超时（秒） | `30` | - |
| `WECHAT_RETRY_TIMES` | 消息重发次数 | `3` | - |

#### AI 配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `DEFAULT_MODEL` | 默认模型 | `gpt-4o-mini` | - |
| `MAX_TOKENS` | 最大生成 tokens | `2000` | - |
| `TEMPERATURE` | 生成温度 | `0.7` | 0-2 |
| `STREAM_OUTPUT` | 启用流式输出 | `true` | - |

#### 安全配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `ENABLE_WHITELIST` | 开启白名单 | `false` | 生产环境 `true` |
| `WHITELIST_USERS` | 白名单用户列表 | - | 逗号分隔的 wxid |
| `RATE_LIMIT` | 每分钟限流 | `10` | - |
| `RATE_LIMIT_WINDOW` | 限流窗口（秒） | `60` | - |
| `ENABLE_CONTENT_FILTER` | 开启内容过滤 | `false` | 生产环境 `true` |

#### 数据库配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/chat_history.db` | - |
| `CHROMA_DB_PATH` | ChromaDB 路径 | `./data/chroma` | - |
| `REDIS_URL` | Redis 连接字符串 | - | 多节点部署 |

#### 工具配置

| 变量名 | 说明 | 默认值 | 建议值 |
|--------|------|--------|--------|
| `ENABLE_WEATHER_TOOL` | 启用天气工具 | `true` | - |
| `ENABLE_SEARCH_TOOL` | 启用搜索工具 | `true` | - |
| `WEATHER_API_KEY` | 天气 API Key | - | 高德/和风天气 |
| `SEARCH_API_KEY` | 搜索 API Key | - | Tavily/SerpApi |

---

## 🎨 配置文件示例

### 完整 .env 示例

```env
# 应用配置
APP_NAME=WeChat AI Bot
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
WORKERS=4

# AI 配置
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_MODEL=gpt-4o-mini
MAX_TOKENS=2000
TEMPERATURE=0.7
STREAM_OUTPUT=true

# 微信配置
WECHAT_HOOK_URL=http://localhost:8080/hook/wechat
WECHAT_TIMEOUT=30
WECHAT_RETRY_TIMES=3

# 安全配置
ENABLE_WHITELIST=true
WHITELIST_USERS=wxid_123,wxid_456,wxid_789
RATE_LIMIT=10
RATE_LIMIT_WINDOW=60
ENABLE_CONTENT_FILTER=true

# 数据库配置
DATABASE_URL=sqlite:///./data/chat_history.db
CHROMA_DB_PATH=./data/chroma

# 工具配置
ENABLE_WEATHER_TOOL=true
ENABLE_SEARCH_TOOL=true
WEATHER_API_KEY=your-weather-api-key
SEARCH_API_KEY=your-search-api-key

# 可选：多节点部署
REDIS_URL=rediss://default:password@your-redis.upstash.io:6379
NODE_ID=node-1
```

---

## 🔄 配置热重载

部分配置支持热重载，无需重启服务：

```bash
# 触发配置重载
curl -X POST http://localhost:8000/api/v1/config/reload \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

支持的配置：
- 白名单用户列表
- 限流参数
- 内容过滤规则

---

## 📝 配置最佳实践

1. **生产环境**：使用环境变量，不要使用配置文件
2. **密钥管理**：使用 Docker Secrets 或 Vault
3. **多环境**：准备 `.env.development`、`.env.production`
4. **版本控制**：`.env.example` 提交到 Git，`.env` 忽略
5. **最小权限**：API Key 仅启用需要的模型

---

最后更新：2026-08-12
