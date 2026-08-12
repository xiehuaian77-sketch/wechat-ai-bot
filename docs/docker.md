# Docker 部署指南

本文档介绍如何使用 Docker Compose 一键部署 WeChat AI Bot。

---

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 10GB 可用磁盘空间

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xiehuaian77-sketch/wechat-ai-bot.git
cd wechat-ai-bot
```

### 2. 配置环境变量

```bash
cp config/.env.example .env
```

编辑 `.env` 文件，填写必要配置：

```env
# 必需配置
OPENAI_API_KEY=sk-...
# 或 DeepSeek
DEEPSEEK_API_KEY=sk-...
# 或 Claude
ANTHROPIC_API_KEY=sk-ant-...

# 可选配置
ENABLE_WHITELIST=true
WHITELIST_USERS=wxid_123,wxid_456
RATE_LIMIT=10
```

### 3. 启动服务

```bash
docker compose up -d
```

### 4. 验证部署

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f app

# 测试 API
curl http://localhost:8000/health
```

---

## 📦 服务说明

Docker Compose 包含以下服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `app` | wechat-ai-bot:latest | 8000 | FastAPI 主服务 |
| `chromadb` | chromadb/chroma:latest | 8001 | 向量数据库 |
| `nginx` | nginx:alpine | 80/443 | 反向代理 + HTTPS |

---

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API Key | - | 否 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | 否 |
| `ANTHROPIC_API_KEY` | Claude API Key | - | 否 |
| `ENABLE_WHITELIST` | 开启白名单 | false | 否 |
| `WHITELIST_USERS` | 白名单用户列表 | - | 否 |
| `RATE_LIMIT` | 每分钟限流 | 10 | 否 |
| `LOG_LEVEL` | 日志级别 | INFO | 否 |

### Volume 挂载

```yaml
volumes:
  - ./data:/app/data          # SQLite 数据库 + 对话历史
  - ./logs:/app/logs          # 日志文件
  - ./config:/app/config      # 配置文件
```

---

## 🏗️ 生产环境部署

### 1. 使用 HTTPS

```bash
# 放置 SSL 证书
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/
cp your-key.pem nginx/ssl/

# 启动
docker compose -f docker-compose.prod.yml up -d
```

### 2. 资源限制

在 `docker-compose.prod.yml` 中配置资源限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. 日志管理

```bash
# 配置日志轮转
docker compose down
docker compose up -d --force-recreate
```

---

## 🔄 更新部署

### 1. 拉取最新代码

```bash
git pull origin main
```

### 2. 重新构建镜像

```bash
docker compose build
```

### 3. 重启服务

```bash
docker compose up -d --force-recreate
```

---

## 📊 监控与运维

### 查看日志

```bash
# 实时日志
docker compose logs -f app

# 最近 100 行
docker compose logs --tail=100 app
```

### 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db
```

### 备份数据

```bash
# 备份 SQLite 数据库
docker compose exec app cp /app/data/chat_history.db /backup/

# 备份 ChromaDB
docker compose exec chromadb cp /chroma/chroma /backup/
```

---

## 🆘 常见问题

### 1. 端口冲突

如果 8000 端口被占用：

```bash
# 修改 docker-compose.yml
ports:
  - "8002:8000"  # 宿主机端口 8002
```

### 2. 内存不足

ChromaDB 需要较多内存，建议至少 4GB：

```bash
# 检查内存使用
docker stats

# 调整 ChromaDB 内存
docker compose exec chromadb chroma --max-memory 2G
```

### 3. 权限问题

```bash
# 修复数据目录权限
sudo chown -R 1000:1000 ./data ./logs
```

---

## 🚢 多节点部署

参考 [docs/multi-node.md](multi-node.md) 了解多节点部署方案。

---

## 📚 参考资料

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)

---

最后更新：2026-08-12
