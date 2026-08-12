# 项目长期记忆

## 测试与 CI
- 测试框架：pytest + anyio，httpx ASGITransport
- 数据库测试：必须使用 `app.database.session.engine` 建表，不要创建独立 engine
- 当前状态：21 passed（health 2 + api 6 + knowledge 2 + middleware 2 + tools 9）
- CI 作业：lint-and-test / security-audit / dependency-review / build
- 所需 GitHub Secrets：`SENTRY_DSN`, `CODECOV_TOKEN`, `NPM_TOKEN`

## 开源文档清单
- CHANGELOG.md / CODE_OF_CONDUCT.md / CONTRIBUTING.md / SECURITY.md / SECURITY_AUDIT.md
- README.md（中文）+ README.en.md（英文）
- docs/architecture.md + docs/development.md
- .github/workflows/ci.yml + release.yml（semantic-release）
- .releaserc.yml（conventionalcommits 预设）
- .github/ISSUE_TEMPLATE/（bug_report.yml, feature_request.yml）
- .github/PULL_REQUEST_TEMPLATE.md
- .github/dependabot.yml（pip + github-actions）
- .pre-commit-config.yaml（ruff + hooks）

## 开源必备文件（已完成）
- ✅ LICENSE（MIT）
- ✅ .gitignore（完整）
- ✅ pyproject.toml（classifiers + urls + 强化 ruff 规则）
- ✅ Dockerfile（多阶段构建 + 非 root）
- ✅ docker-compose.yml（含 healthcheck）
- ✅ Git 仓库已初始化，首次提交完成（92 files, 10562 insertions）

## 关键代码约定
- FastAPI startup 事件中初始化数据库表（生产环境多 worker 模式跳过）
- 测试环境需在 conftest 手动调用 `Base.metadata.create_all`
- JWT 认证依赖 `get_session`，测试需共享同一 engine
- `on_event("startup")` 已弃用，待迁移到 lifespan
- ruff 配置已强化：SIM / RET / ARG / PTH / RUF 规则集已启用

## 已修复问题
- httpx AsyncClient 不再接受 `app=` 参数，必须用 `ASGITransport`
- `JSONResponse` / `ToolResult` 缺失 import 导致 NameError
- rate_limit 断言需用子串匹配（IP limiter 与全局 limiter 消息不同）
- 数据库测试 schema 初始化：使用 `app.database.session.engine` 而非独立 engine

## 精进完成时间
- 2025-08-12：达到完美开源级别，所有测试通过，文档齐全，CI/CD 完整
