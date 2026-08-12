# Contributing to WeChat AI Bot

感谢你对 WeChat AI Bot 的关注！我们欢迎所有形式的贡献。

## 🚀 5 分钟快速贡献

1. **Fork** 本仓库
2. 创建分支：`git checkout -b feat/your-feature`
3. 提交：`git commit -m "feat: add your feature"`
4. 推送：`git push origin feat/your-feature`
5. **提一个 PR**，等待 Review

## 📋 开发环境准备

```bash
# 克隆仓库
git clone https://github.com/xiehuaian77-sketch/wechat-ai-bot.git
cd wechat-ai-bot

# 安装依赖（推荐使用 uv）
uv sync

# 复制环境变量
cp config/.env.example .env

# 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
uv run pytest tests/ -v
```

## 🧪 测试规范

- 新功能必须补充单元测试
- 提交前确保 `uv run ruff check app/ tests/` 通过
- 提交前确保 `uv run mypy app/ --ignore-missing-imports` 通过
- 提交前确保 `uv run pytest tests/ -v` 全部通过

## 📝 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档改进
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建/工具/依赖更新

示例：
```
feat: add Battle Mode for dual model comparison
fix: handle empty wechat message payload
docs: update README with deployment steps
```

## 🎯 贡献类型

| 类型 | 说明 | 标签 |
|------|------|------|
| 🐛 Bug 修复 | 修复现有功能的问题 | `bug` |
| ✨ 新功能 | 新增功能模块 | `enhancement` |
| 📝 文档改进 | 错别字、补充示例、翻译 | `documentation` |
| 🎨 UI/UX | 前端界面优化 | `ui` |
| 🔧 DevOps | Docker、CI/CD、监控 | `devops` |
| 🧪 测试 | 单元测试、集成测试 | `testing` |
| 🎭 Chatflow | 新增或优化人设编排 | `chatflow` |

### Chatflow 贡献指南

欢迎贡献新的 Chatflow 模板或优化现有模板！

1. **新增模板**：在 `config/chatflow/` 目录下创建 `.yaml` 文件
2. **测试模板**：使用管理后台的 Chatflow 编辑器测试
3. **提交 PR**：标签使用 `chatflow`
4. **文档说明**：在 PR 描述中说明模板的用途和配置示例

参考 [Chatflow 文档](docs/chatflow.md) 了解详细配置。

## 💡 没有头绪？

看看我们的 [Ideas 列表](https://github.com/xiehuaian77-sketch/wechat-ai-bot/discussions/categories/ideas) 或 [Good First Issues](https://github.com/xiehuaian77-sketch/wechat-ai-bot/labels/good%20first%20issue)。

## 🤝 行为准则

本项目遵循 [Contributor Covenant](CODE_OF_CONDUCT.md)。参与本项目即表示你同意遵守其条款。

## ❓ 问题与讨论

- **Bug 报告**：[GitHub Issues](https://github.com/xiehuaian77-sketch/wechat-ai-bot/issues)
- **功能请求**：[GitHub Discussions](https://github.com/xiehuaian77-sketch/wechat-ai-bot/discussions)
- **技术交流**：欢迎在 Discussions 中发起讨论
