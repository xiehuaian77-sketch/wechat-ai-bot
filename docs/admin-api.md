# 管理后台 API

本文档介绍 WeChat AI Bot 管理后台的 REST API。

---

## 🔐 认证

所有管理 API 都需要 Bearer Token：

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/users
```

获取 Token：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

---

## 📊 API 列表

### 用户管理

#### 获取用户列表

```http
GET /api/v1/admin/users
```

响应：

```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "wxid": "wxid_123",
      "nickname": "张三",
      "role": "user",
      "created_at": "2026-08-01T10:00:00Z",
      "last_active": "2026-08-12T10:00:00Z"
    }
  ]
}
```

#### 获取用户详情

```http
GET /api/v1/admin/users/{wxid}
```

#### 更新用户角色

```http
PUT /api/v1/admin/users/{wxid}
Content-Type: application/json

{
  "role": "admin"
}
```

#### 删除用户

```http
DELETE /api/v1/admin/users/{wxid}
```

---

### 机器人管理

#### 获取机器人列表

```http
GET /api/v1/admin/bots
```

响应：

```json
[
  {
    "bot_id": "bot_001",
    "wxid": "wxid_bot1",
    "nickname": "AI助手",
    "status": "online",
    "node_id": "node-1",
    "created_at": "2026-08-01T10:00:00Z"
  }
]
```

#### 创建机器人

```http
POST /api/v1/admin/bots
Content-Type: application/json

{
  "wxid": "wxid_bot2",
  "nickname": "AI助手2"
}
```

#### 删除机器人

```http
DELETE /api/v1/admin/bots/{bot_id}
```

---

### Token 用量统计

#### 获取 Token 统计

```http
GET /api/v1/admin/tokens/usage
```

查询参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `start_date` | 开始日期 | `2026-08-01` |
| `end_date` | 结束日期 | `2026-08-12` |
| `granularity` | 粒度 | `day` / `hour` |

响应：

```json
{
  "total_tokens": 150000,
  "prompt_tokens": 100000,
  "completion_tokens": 50000,
  "daily": [
    {
      "date": "2026-08-12",
      "tokens": 15000,
      "requests": 100
    }
  ]
}
```

---

### 节点管理

#### 获取节点列表

```http
GET /api/v1/admin/nodes
```

响应：

```json
[
  {
    "node_id": "node-1",
    "status": "healthy",
    "cpu_usage": 45,
    "memory_usage": 60,
    "disk_usage": 30,
    "last_heartbeat": "2026-08-12T10:00:00Z"
  }
]
```

#### 重启节点

```http
POST /api/v1/admin/nodes/{node_id}/restart
```

---

### 日志管理

#### 查询日志

```http
GET /api/v1/admin/logs
```

查询参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `level` | 日志级别 | `INFO` / `ERROR` |
| `start_time` | 开始时间 | `2026-08-12T00:00:00Z` |
| `end_time` | 结束时间 | `2026-08-12T23:59:59Z` |
| `keyword` | 关键词 | `token` |
| `page` | 页码 | `1` |
| `page_size` | 每页数量 | `20` |

响应：

```json
{
  "total": 1000,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "timestamp": "2026-08-12T10:00:00Z",
      "level": "INFO",
      "message": "Message received from wxid_123",
      "metadata": {}
    }
  ]
}
```

#### 导出日志

```http
GET /api/v1/admin/logs/export
```

响应：`text/plain` 格式的日志文件

---

### 系统配置

#### 获取配置

```http
GET /api/v1/admin/config
```

响应：

```json
{
  "app": {
    "name": "WeChat AI Bot",
    "version": "0.1.0"
  },
  "llm": {
    "default_provider": "openai",
    "providers": ["openai", "deepseek", "anthropic"]
  },
  "security": {
    "enable_whitelist": true,
    "rate_limit": 10
  }
}
```

#### 更新配置

```http
PUT /api/v1/admin/config
Content-Type: application/json

{
  "security": {
    "enable_whitelist": true,
    "rate_limit": 20
  }
}
```

---

### 统计面板

#### 获取仪表盘数据

```http
GET /api/v1/admin/dashboard
```

响应：

```json
{
  "active_users": 50,
  "messages_today": 500,
  "tokens_today": 50000,
  "api_calls_today": 300,
  "error_rate": 0.01,
  "top_users": [
    {
      "wxid": "wxid_123",
      "messages": 50
    }
  ],
  "model_usage": [
    {
      "model": "gpt-4o-mini",
      "calls": 200
    }
  ]
}
```

---

## 📝 错误码

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | `INVALID_REQUEST` | 请求参数错误 |
| 401 | `UNAUTHORIZED` | 未认证或 Token 过期 |
| 403 | `FORBIDDEN` | 无权限访问 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 429 | `RATE_LIMITED` | 请求过多 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

---

## 🚨 限流

管理 API 也有严格限流：

- 认证端点：10 次/分钟
- 其他端点：100 次/分钟

超过限流返回 `429 Too Many Requests`。

---

最后更新：2026-08-12
