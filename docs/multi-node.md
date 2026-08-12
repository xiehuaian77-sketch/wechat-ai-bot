# 多节点部署指南

本文档介绍如何部署多个 WeChat AI Bot 节点，实现负载均衡和高可用。

---

## 🎯 多节点架构

```
                    ┌─────────────────┐
                    │  Cloudflare     │
                    │  Worker LB      │
                    │  (负载均衡)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
         │ Node-1  │    │ Node-2  │    │ Node-3  │
         │ (Docker)│    │ (Docker)│    │ (Docker)│
         └────┬────┘    └────┬────┘    └────┬────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Upstash Redis  │
                    │  (共享数据层)    │
                    └─────────────────┘
```

**核心设计**：
- 所有节点运行**同一 Docker 镜像**，无状态设计
- 共享同一个 Upstash Redis（或自建 Redis 集群）
- Cloudflare Worker 负责健康检查与轮询分流
- 源站 IP 仅存储在 Worker 中，不对外暴露

---

## 📋 前置要求

- 一个域名（如 `bot.your-domain.com`）
- Cloudflare 账号（用于 Worker 和 DNS）
- Upstash Redis 账号（或自建 Redis）
- 2+ 台服务器（或 Docker 容器）

---

## 🚀 快速部署

### 1. 准备 Upstash Redis

1. 访问 [Upstash Console](https://console.upstash.com/)
2. 创建新 Redis 实例
3. 复制 Redis URL（格式：`rediss://default:password@your-redis.upstash.io:6379`）

### 2. 部署节点

在所有服务器上执行：

```bash
# 克隆项目
git clone https://github.com/xiehuaian77-sketch/wechat-ai-bot.git
cd wechat-ai-bot

# 配置环境变量
cp config/.env.example .env

# 编辑 .env
REDIS_URL=rediss://default:password@your-redis.upstash.io:6379
NODE_ID=node-1  # 每个节点唯一

# 启动服务
docker compose up -d
```

### 3. 部署 Cloudflare Worker

1. 克隆 Worker 代码：

```bash
git clone https://github.com/xiehuaian77-sketch/wechat-ai-bot.git
cd wechat-ai-bot/cloudflare-worker
```

2. 配置 Worker：

```javascript
export default {
  async fetch(request, env) {
    const ORIGINS = [
      'https://node1.your-domain.com',
      'https://node2.your-domain.com',
      'https://node3.your-domain.com',
    ];

    // 轮询分流
    const index = Math.floor(Math.random() * ORIGINS.length);
    const target = ORIGINS[index];

    // 健康检查（可选）
    // await healthCheck(target);

    return fetch(target + request.url, request);
  }
};
```

3. 部署 Worker：

```bash
npm install -g wrangler
wrangler login
wrangler publish
```

4. 配置 DNS：
   - 在 Cloudflare DNS 中创建 CNAME 记录：`bot.your-domain.com` → `your-worker.your-domain.com`

---

## 🔧 配置说明

### 共享 Redis 配置

所有节点必须使用**同一个 Redis**：

```env
# .env（所有节点相同）
REDIS_URL=rediss://default:password@your-redis.upstash.io:6379
REDIS_PREFIX=wechat-ai-bot  # 共享前缀，避免多项目冲突
```

### 节点标识

每个节点必须有**唯一标识**：

```env
# Node-1
NODE_ID=node-1

# Node-2
NODE_ID=node-2

# Node-3
NODE_ID=node-3
```

### 会话亲和性（可选）

如果需要会话亲和性（同一用户固定到同一节点）：

```javascript
// Cloudflare Worker
const userId = request.headers.get('X-User-ID');
const index = hashCode(userId) % ORIGINS.length;
const target = ORIGINS[index];
```

---

## 📊 监控与运维

### 健康检查

每个节点提供健康检查端点：

```bash
curl https://node1.your-domain.com/health
```

响应：

```json
{
  "status": "healthy",
  "node_id": "node-1",
  "redis": "connected",
  "timestamp": "2026-08-12T10:00:00Z"
}
```

### 节点管理

```bash
# 查看所有节点状态
./scripts/node-status.sh

# 重启指定节点
./scripts/node-restart.sh node-2

# 滚动更新
./scripts/rolling-update.sh
```

### 日志聚合

推荐使用 ELK 或 Loki 聚合日志：

```bash
# 使用 Loki
docker compose -f docker-compose.logging.yml up -d
```

---

## 🔄 滚动更新

无停机更新所有节点：

```bash
#!/bin/bash
# rolling-update.sh

NODES=("node-1" "node-2" "node-3")

for node in "${NODES[@]}"; do
  echo "Updating $node..."

  # 从负载均衡中移除
  ./scripts/drain-node.sh $node

  # 更新代码
  ssh user@node-$node "cd wechat-ai-bot && git pull && docker compose up -d"

  # 健康检查
  sleep 30
  ./scripts/health-check.sh $node

  # 重新加入负载均衡
  ./scripts/restore-node.sh $node

  echo "$node updated successfully"
done
```

---

## 🆘 故障排查

### 1. 节点无法连接 Redis

```bash
# 检查 Redis 连接
docker compose exec app redis-cli -u $REDIS_URL ping

# 检查网络
docker network inspect wechat-ai-bot_default
```

### 2. 负载均衡不均

```bash
# 查看 Worker 日志
wrangler tail

# 检查 ORIGINS 配置
wrangler secret put ORIGINS
```

### 3. 数据不一致

```bash
# 检查 Redis 数据
redis-cli -u $REDIS_URL KEYS "*"

# 清空缓存（谨慎操作）
redis-cli -u $REDIS_URL FLUSHDB
```

---

## 📈 性能优化

### 1. 节点数量建议

| 用户量 | 建议节点数 | Redis 配置 |
|--------|------------|------------|
| < 100 | 1 | Upstash Free |
| 100-1000 | 2-3 | Upstash Pay-as-you-go |
| 1000-10000 | 5-10 | Upstash Pro |
| > 10000 | 10+ | 自建 Redis Cluster |

### 2. 资源要求

每个节点：

- CPU：2 cores
- 内存：4GB
- 磁盘：20GB
- 网络：100Mbps

### 3. 缓存策略

```bash
# 启用 Redis 缓存
ENABLE_CACHE=true
CACHE_TTL=3600  # 1 小时

# 热点数据预加载
./scripts/preload-cache.sh
```

---

## 🔒 安全考虑

- 所有节点使用**同一镜像**，避免配置漂移
- 源站 IP 仅存储在 Worker 中，不对外暴露
- 节点间通信通过 Redis，不直接暴露端口
- 使用 Upstash Redis 的 TLS 加密连接

---

## 📚 参考资料

- [Cloudflare Worker 文档](https://developers.cloudflare.com/workers/)
- [Upstash Redis 文档](https://upstash.com/docs/redis)
- [Docker 多阶段构建](https://docs.docker.com/build/building/multi-stage/)

---

最后更新：2026-08-12
