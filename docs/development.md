# 开发指南

## 环境要求

- Python >= 3.12
- Node.js >= 18（如需前端构建）
- Docker & Docker Compose（生产部署）

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/xiehuaian77-sketch/neural-ai-browser.git
cd wechat-ai-bot

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要的 API Key

# 5. 运行测试
pytest tests/

# 6. 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

## 代码规范

- **格式化**：`ruff format .`
- **Lint**：`ruff check .`
- **类型检查**：`mypy app/`
- **测试**：`pytest tests/ -v`
- **提交信息**：Conventional Commits（`feat:`, `fix:`, `docs:` 等）

## 项目结构

```
wechat-ai-bot/
├── app/                  # 应用代码
│   ├── agent/           # Agent 核心逻辑
│   ├── api/             # API 路由
│   ├── auth/            # 认证授权
│   ├── context/         # 上下文管理
│   ├── database/        # 数据库模型
│   ├── knowledge/       # 知识库
│   ├── middleware/      # 中间件
│   ├── models/          # Pydantic 模型
│   ├── routers/         # 业务路由
│   ├── services/        # 业务服务
│   └── tools/           # 工具定义
├── tests/               # 测试
│   ├── unit/           # 单元测试
│   └── conftest.py     # 测试夹具
├── config/              # 配置
├── docs/                # 文档
├── .github/             # CI/CD 配置
├── pyproject.toml       # 项目配置
├── Dockerfile           # 容器镜像
└── docker-compose.yml   # 编排配置
```

## 添加新工具

1. 在 `app/tools/` 创建新文件
2. 继承 `BaseTool` 并实现 `execute()`
3. 在 `app/tools/manager.py` 注册
4. 添加单元测试 `tests/unit/test_tools.py`

## 添加新 API

1. 在 `app/api/` 或 `app/routers/` 创建路由
2. 使用依赖注入获取 `db_session` 和 `current_user`
3. 添加 Pydantic 请求/响应模型
4. 添加集成测试

## 环境变量

详见 `.env.example`。关键变量：

| 变量 | 说明 | 必填 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 否 |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | 否 |
| `DATABASE_URL` | 数据库连接 | 否 |
| `REDIS_URL` | Redis 连接 | 否 |
| `SENTRY_DSN` | Sentry DSN | 否 |
| `SECRET_KEY` | JWT 密钥 | 是 |
