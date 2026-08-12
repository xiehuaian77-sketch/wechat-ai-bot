# 开源发布 Checklist

在公开推送 GitHub 之前，逐项确认以下内容。按优先级分为 P0（必须）、P1（强烈建议）、P2（建议）。

---

## P0 - 必须完成

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | LICENSE 文件 | ✅ | MIT License 已添加 |
| 2 | README.md | ✅ | 包含定位、截图、快速开始、架构图 |
| 3 | 代码可运行 | ✅ | Docker Compose 一键启动 |
| 4 | 无敏感信息 | ✅ | .env 已加入 .gitignore |
| 5 | CI/CD 通过 | ✅ | GitHub Actions 已配置 |

---

## P1 - 强烈建议

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 6 | 在线 Demo | ⏳ | HuggingFace Space / Cloudflare Workers 部署 |
| 7 | 演示 GIF / 视频 | ⏳ | 15-30 秒展示核心功能，放入 README |
| 8 | GitHub Description | ⏳ | 一句话描述 + 关键词 |
| 9 | GitHub Topics | ⏳ | 10+ 个精准标签 |
| 10 | Social Preview | ⏳ | 1280×640 预览图 |
| 11 | Release v0.1.0 | ⏳ | 创建首次 Release |

---

## P2 - 建议完成

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 12 | CODE_OF_CONDUCT.md | ✅ | 已添加 |
| 13 | CONTRIBUTING.md | ✅ | 贡献指南已完善 |
| 14 | SECURITY.md | ✅ | 安全策略已添加 |
| 15 | CHANGELOG.md | ✅ | Keep a Changelog 格式 |
| 16 | Docker Compose | ✅ | 包含 ChromaDB + Nginx |
| 17 | .gitattributes | ✅ | 跨平台换行符统一 |
| 18 | .editorconfig | ✅ | 编辑器配置统一 |
| 19 | Issue Templates | ✅ | Bug 报告 + 功能请求 |
| 20 | PR Template | ✅ | 标准化 PR 描述 |
| 21 | FUNDING.yml | ✅ | 赞助链接配置 |
| 22 | 英文 README | ✅ | README.en.md 已添加 |
| 23 | 代码格式化 | ✅ | ruff + mypy 通过 |
| 24 | 单元测试 | ✅ | 21 个测试全部通过 |

---

## 📋 待办事项

### 本地已完成 ✅
- [x] 代码质量检查（ruff lint / format / mypy / pytest）
- [x] 开源基础文件（LICENSE / README / CONTRIBUTING / SECURITY）
- [x] CI/CD 配置（GitHub Actions）
- [x] Docker 部署配置
- [x] 开发文档（架构图 / 开发指南）
- [x] Issue / PR 模板
- [x] .gitignore / .gitattributes / .editorconfig

### 需用户在 GitHub 网页操作 ⏳
- [ ] 设置仓库 Description
- [ ] 添加 Topics 标签
- [ ] 上传 Social Preview 图
- [ ] 启用 Discussions
- [ ] 创建 Release v0.1.0

### 需准备素材 🎨
- [ ] 录制演示 GIF（参考 DEMO_GUIDE.md）
- [ ] 准备主界面截图
- [ ] 部署在线 Demo（参考 GITHUB_SETUP.md）

---

## 🚀 发布流程

1. **本地确认**：`git status` 无未提交文件
2. **推送代码**：`git push origin main`
3. **GitHub 配置**：按 `docs/GITHUB_SETUP.md` 操作
4. **制作素材**：按 `DEMO_GUIDE.md` 录制演示
5. **推广发布**：
   - Hacker News（Show HN）
   - V2EX（分享创造）
   - 掘金（技术文章）
   - Reddit（r/MachineLearning / r/FastAPI）

---

## 📞 需要帮助？

- GitHub 配置问题 → 查看 `docs/GITHUB_SETUP.md`
- 录制演示视频 → 查看 `DEMO_GUIDE.md`
- 截图素材要求 → 查看 `assets/README.md`
