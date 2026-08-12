# 安全与合规

WeChat AI Bot 是一个基于 ComWeChatRobot 的 AI 微信助手框架。使用本项目的用户需要了解以下安全与合规要点。

---

## 🔒 安全特性

### 数据安全
- **本地存储优先**：所有对话历史、向量数据默认存储在本地 SQLite + ChromaDB，不上传云端
- **密钥隔离**：API Key 通过 `.env` 管理，不写入代码仓库，不上传到任何第三方服务
- **权限控制**：支持管理员白名单/黑名单，防止未授权访问
- **限流保护**：内置熔断器 + 自动重连 + 限流机制，防止 API 滥用

### 隐私保护
- **P2P 对话隔离**：管理员可配置用户私聊权限，避免公共会话泄露
- **敏感信息过滤**：日志系统自动脱敏 API Key、Token 等凭证信息
- **可审计日志**：所有 API 调用和消息事件均有结构化日志，支持安全审计

### 部署安全
- **Docker 隔离**：所有服务运行在容器内，宿主机仅暴露必要端口
- **Nginx 反向代理**：支持 HTTPS 配置，API 通信加密
- **环境变量管理**：生产环境推荐使用 Docker Secrets 或环境变量注入

---

## ⚠️ 风险提示

### 1. 微信封号风险

**重要**：本项目通过 ComWeChatRobot 框架实现微信 PC 客户端自动化，存在一定的封号风险。

| 风险因素 | 影响等级 | 缓解措施 |
|----------|----------|----------|
| 高频消息发送 | 🔴 高 | 内置限流 + 随机延迟 + 白名单机制 |
| 非正常操作行为 | 🔴 高 | 模拟人工操作间隔，避免批量操作 |
| 多开/多实例 | 🟡 中 | 单实例多 Bot 架构，避免多开 |
| 敏感内容回复 | 🟡 中 | 内置内容过滤 + 管理员审核 |

**建议**：
- 仅在个人号上测试使用，避免在主号上部署
- 开启白名单机制，仅允许信任的用户与 Bot 交互
- 监控日志，发现异常及时调整策略
- 遵守微信用户协议，不用于商业营销或骚扰行为

### 2. AI 内容合规

- AI 生成的内容可能包含错误信息或不当言论，请人工审核后转发
- 建议配置内容过滤规则，避免回复敏感话题
- 知识库上传的文档请确保拥有版权或授权

### 3. API 密钥安全

- **不要**将 `.env` 文件提交到 Git
- **不要**在代码中硬编码 API Key
- 定期轮换 API Key，特别是在团队协作场景
- 使用具有最小权限的 API Key（仅启用需要的模型）

### 4. 数据备份

- 定期备份 SQLite 数据库和 ChromaDB 向量数据
- Docker 部署时建议挂载 volume 持久化存储
- 生产环境考虑使用 PostgreSQL + 外部向量数据库

---

## 🛡️ 安全最佳实践

### 1. 白名单机制（必开）

```bash
# .env
ENABLE_WHITELIST=true
WHITELIST_USERS=wxid_123,wxid_456  # 仅允许这些用户
```

### 2. 限流配置

```bash
# .env
RATE_LIMIT=10  # 每分钟最多 10 条消息
RATE_LIMIT_WINDOW=60  # 限流窗口（秒）
```

### 3. 日志脱敏

```bash
# .env
LOG_LEVEL=INFO  # 生产环境建议 INFO，开发环境可用 DEBUG
REDACT_SENSITIVE=true  # 自动脱敏 API Key、Token
```

### 4. 网络隔离

- 生产环境不要将 FastAPI 端口（8000）直接暴露到公网
- 使用 Nginx 反向代理 + HTTPS
- Docker Compose 使用内部网络隔离

---

## 📋 安全审计清单

在首次部署前，请确认以下安全配置：

- [ ] `.env` 文件已配置，未提交到 Git
- [ ] `ENABLE_WHITELIST=true` 已开启
- [ ] `WHITELIST_USERS` 已填写信任用户列表
- [ ] `RATE_LIMIT` 已配置合理值
- [ ] `LOG_LEVEL=INFO`（生产环境）
- [ ] Docker 端口仅暴露必要端口
- [ ] HTTPS 已配置（生产环境）
- [ ] 已设置定期备份策略
- [ ] API Key 具有最小权限
- [ ] 已测试封号风险缓解措施

---

## 🚨 漏洞报告

如果你发现安全漏洞，请通过以下方式报告：

1. **GitHub Security Advisory**：在仓库的 "Security" 标签页提交 Private vulnerability report
2. **邮件**：发送邮件至 security@your-domain.com（请替换为实际邮箱）
3. **不要**在公开 Issue 中披露安全漏洞

我们会在 48 小时内响应，并在修复后发布安全公告。

---

## 📜 合规声明

1. **本项目的合法性**：本项目仅提供技术框架，使用者需自行遵守当地法律法规和微信用户协议
2. **AI 生成内容**：AI 生成的内容不代表本项目立场，使用者需自行承担内容责任
3. **第三方服务**：本项目集成了第三方 AI 服务（OpenAI、DeepSeek 等），使用前请阅读其服务条款
4. **许可证**：本项目采用 MIT License，详见 [LICENSE](LICENSE) 文件

---

## 📚 参考资料

- [ComWeChatRobot 使用条款](https://github.com/WeChat-Shot/ComWeChatRobot)
- [微信个人账号使用规范](https://weixin.qq.com/cgi-bin/readtemplate?t=weixin_agreement&s=default)
- [OpenAI 使用政策](https://openai.com/policies/usage-policies)
- [MIT License 说明](https://opensource.org/licenses/MIT)

---

最后更新：2026-08-12
