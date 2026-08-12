# 架构文档

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌────────────────┐
│   Nginx     │────▶│  FastAPI    │────▶│  LLM Providers │
│ (Reverse)   │     │   App       │     │ (OpenAI/etc)   │
└─────────────┘     └──────┬──────┘     └────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ SQLite   │ │ ChromaDB │ │  Redis   │
        │ (Users,  │ │ (RAG     │ │ (Cache,  │
        │  Msgs)   │ │  Vectors)│ │  Queue)  │
        └──────────┘ └──────────┘ └──────────┘
```

## 核心模块

| 模块 | 路径 | 职责 |
|------|------|------|
| Agent Engine | `app/agent/` | LangGraph 状态机编排 |
| API Router | `app/api/` | RESTful 接口定义 |
| Auth | `app/auth/` | JWT 认证与 RBAC |
| Database | `app/database/` | SQLAlchemy ORM 模型与会话 |
| Knowledge | `app/knowledge/` | 文档解析、分块、向量化 |
| Middleware | `app/middleware/` | 限流、CORS、日志 |
| Services | `app/services/` | AI Provider、消息处理 |
| Tools | `app/tools/` | 可执行工具注册与调用 |

## Agent 工作流

```
StateGraph (planner → executor → reflector → responder)
```

1. **Planner**：解析用户意图，生成任务计划
2. **Executor**：调用工具执行子任务
3. **Reflector**：反思执行结果，调整策略
4. **Responder**：生成最终回复

## 数据流

1. 用户消息通过 WebSocket/HTTP 进入
2. Auth 中间件验证身份
3. RateLimit 中间件限流
4. Router 分发到对应端点
5. Agent Engine 处理（可选 RAG）
6. 结果持久化到数据库
7. 返回响应

## 部署架构

- **开发**：本地 `uvicorn` + SQLite
- **生产**：Docker Compose（App + Redis + Nginx）
- **扩展**：支持多 Worker 进程
