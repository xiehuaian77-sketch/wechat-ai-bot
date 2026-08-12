# 项目长期记忆

## 测试与 CI
- 测试框架：pytest + anyio，httpx ASGITransport
- 数据库测试：必须使用 `app.database.session.engine` 建表，不要创建独立 engine
- 当前状态：21 passed（health 2 + api 6 + knowledge 2 + middleware 2 + tools 9）
- CI 作业：lint-and-test / security-audit / dependency-review / build
- 所需 GitHub Secrets：`SENTRY_DSN`, `CODECOV_TOKEN`, `NPM_TOKEN`

## 开源文档清单
- CHANGELOG.md / CODE_OF_CONDUCT.md / CONTRIBUTING.md / SECURITY.md
- README.md（中文）+ README.en.md（英文）
- .github/workflows/ci.yml + release.yml（semantic-release）
- .releaserc.yml（conventionalcommits 预设）

## 关键代码约定
- FastAPI startup 事件中初始化数据库表（生产环境多 worker 模式跳过）
- 测试环境需在 conftest 手动调用 `Base.metadata.create_all`
- JWT 认证依赖 `get_session`，测试需共享同一 engine
- `on_event("startup")` 已弃用，待迁移到 lifespan

## 已修复问题
- httpx AsyncClient 不再接受 `app=` 参数，必须用 `ASGITransport`
- `JSONResponse` / `ToolResult` 缺失 import 导致 NameError
- rate_limit 断言需用子串匹配（IP limiter 与全局 limiter 消息不同）
