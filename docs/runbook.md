# 运维手册

本文档提供 WeChat AI Bot 的生产环境运维指南，包括监控、备份、故障排查等。

---

## 📊 监控指标

### 1. 系统指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| CPU 使用率 | 进程 CPU 占用 | > 80% |
| 内存使用率 | 进程内存占用 | > 90% |
| 磁盘使用率 | 数据目录磁盘占用 | > 85% |
| 网络带宽 | 入站/出站流量 | > 100Mbps |

### 2. 应用指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| API 响应时间 | P95 响应时间 | > 2s |
| API 错误率 | 5xx 错误占比 | > 1% |
| 消息吞吐量 | 每秒处理消息数 | < 10 msg/s |
| LLM 调用延迟 | AI 模型响应时间 | > 10s |

### 3. 业务指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 活跃用户数 | 日活跃用户 | - |
| 消息成功率 | 成功发送消息占比 | < 95% |
| 限流触发次数 | 每分钟限流次数 | > 50 次 |
| 白名单拒绝次数 | 未授权用户请求数 | > 100 次 |

---

## 🛠️ 日常运维

### 1. 日志查看

```bash
# 实时日志
docker compose logs -f app

# 最近 100 行
docker compose logs --tail=100 app

# 错误日志
docker compose logs app | grep ERROR
```

### 2. 数据备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/wechat-ai-bot/$DATE"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 SQLite 数据库
docker compose exec app cp /app/data/chat_history.db $BACKUP_DIR/

# 备份 ChromaDB
docker compose exec chromadb tar czf $BACKUP_DIR/chroma.tar.gz /chroma/chroma

# 备份配置
cp .env $BACKUP_DIR/
cp -r config/ $BACKUP_DIR/

# 压缩备份
tar czf /backup/wechat-ai-bot-$DATE.tar.gz $BACKUP_DIR

# 清理 7 天前的备份
find /backup -type d -mtime +7 -exec rm -rf {} +
```

### 3. 数据恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE="/backup/wechat-ai-bot-20260812.tar.gz"

# 停止服务
docker compose down

# 恢复数据
tar xzf $BACKUP_FILE
docker compose cp restored/chat_history.db app:/app/data/
docker compose cp restored/chroma chromadb:/chroma/

# 重启服务
docker compose up -d
```

---

## 🔄 更新流程

### 1. 滚动更新（推荐）

```bash
#!/bin/bash
# rolling-update.sh

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose build

# 逐个重启服务
services=("app" "chromadb" "nginx")

for service in "${services[@]}"; do
  echo "Updating $service..."

  # 重启服务
  docker compose up -d --force-recreate $service

  # 健康检查
  sleep 30
  if ! curl -f http://localhost:8000/health; then
    echo "Health check failed for $service"
    exit 1
  fi

  echo "$service updated successfully"
done
```

### 2. 蓝绿部署

```bash
# 1. 部署新版本（蓝）
docker compose -f docker-compose.blue.yml up -d

# 2. 健康检查
curl -f http://blue.your-domain.com/health

# 3. 切换流量
./scripts/switch-traffic.sh blue

# 4. 下线旧版本（绿）
docker compose -f docker-compose.green.yml down
```

---

## 🚨 故障排查

### 1. 服务无法启动

```bash
# 检查日志
docker compose logs app

# 检查配置
docker compose config

# 检查端口占用
netstat -tlnp | grep 8000
```

### 2. 高内存使用

```bash
# 查看内存使用
docker stats

# 重启服务
docker compose restart app

# 检查内存泄漏
docker compose exec app python -m memory_profiler app/main.py
```

### 3. 数据库连接失败

```bash
# 检查 ChromaDB 状态
curl http://localhost:8001/api/v1/heartbeat

# 检查 Redis 连接
docker compose exec redis redis-cli ping

# 重启数据库
docker compose restart chromadb redis
```

---

## 📈 性能优化

### 1. 数据库优化

```bash
# 清理旧数据
docker compose exec app python -m scripts.cleanup_old_data --days 30

# 优化 ChromaDB
docker compose exec chromadb python -m scripts.optimize_db

# 重建索引
docker compose exec app python -m scripts.rebuild_index
```

### 2. 缓存优化

```bash
# 预热缓存
docker compose exec app python -m scripts.warmup_cache

# 清理缓存
docker compose exec app python -m scripts.clear_cache
```

### 3. 资源调整

```bash
# 调整 Docker 资源限制
docker compose down
docker compose up -d --scale app=2
```

---

## 🔒 安全运维

### 1. 证书管理

```bash
# 自动续期 Let's Encrypt 证书
certbot renew --dry-run

# 部署新证书
docker compose exec nginx nginx -s reload
```

### 2. 密钥轮换

```bash
# 生成新 API Key
openssl rand -hex 32

# 更新环境变量
docker compose down
vim .env
docker compose up -d
```

### 3. 审计日志

```bash
# 导出审计日志
docker compose exec app python -m scripts.export_audit_log --days 7

# 分析日志
docker compose exec app python -m scripts.analyze_logs
```

---

## 📞 应急联系

- **负责人**：your-name
- **邮箱**：your-email@example.com
- **电话**：your-phone
- **备用联系人**：backup-name

---

## 📋 运维 Checklist

### 每日
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 确认备份完成

### 每周
- [ ] 检查磁盘使用率
- [ ] 分析性能指标
- [ ] 清理临时文件

### 每月
- [ ] 安全补丁更新
- [ ] 密钥轮换
- [ ] 备份恢复测试

### 每季度
- [ ] 容量规划
- [ ] 架构评审
- [ ] 应急演练

---

最后更新：2026-08-12
