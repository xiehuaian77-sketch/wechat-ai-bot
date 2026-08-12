# GitHub 仓库配置指南

完成代码上传后，按以下步骤配置仓库，提升项目曝光度和专业性。

---

## 1. 基本信息设置

进入仓库页面 → 点击右上角 **Settings**（设置）

### Description（描述）
```
基于 AI 的微信智能助手 | ComWeChatRobot + FastAPI + LangGraph + ChromaDB
```

### Website（网站）
如果有部署的 Demo 或文档站点，填写 URL。例如：
- HuggingFace Space: `https://huggingface.co/spaces/你的用户名/wechat-ai-bot`
- 自建文档站: `https://docs.xxx.com`

### Topics（标签）⭐ 最重要
添加以下标签（每个标签按回车确认）：

```
fastapi
langgraph
chromadb
wechat-bot
ai-agent
rag
llm
openai
deepseek
claude
python
docker
chatbot
vector-database
```

**作用**：用户通过 Topics 发现项目，GitHub Trending 也依赖 Topics 分类。

---

## 2. 社交预览图（Social Preview）

GitHub 仓库顶部 → 点击相机图标上传预览图。

**规格要求**：
- 尺寸：`1280 × 640 px`
- 格式：PNG 或 JPG
- 内容建议：
  - 项目 Logo + 一句话定位
  - 或主界面截图
  - 或架构图

**工具推荐**：
- [Canva](https://www.canva.com/) 在线设计
- [Figma](https://www.figma.com/) 专业设计
- 简单方案：截一张主界面，用系统画图工具裁剪为 1280×640

**分享效果**：
- 分享到 Twitter/X 时自动显示
- 分享到掘金、V2EX 时自动抓取
- 出现在 GitHub Trending 时展示

---

## 3. 启用 GitHub Pages（可选）

Settings → Pages → Source 选择 `Deploy from a branch` → Branch 选 `main` → `/docs` 文件夹

这样 `https://xiehuaian77-sketch.github.io/wechat-ai-bot/` 可访问文档站点。

---

## 4. 启用 Discussions（讨论区）

Settings → General → Features → 勾选 **Discussions**

**作用**：
- 建立 Q&A 社区
- 用户可直接提问，减少 Issues 噪音
- 可创建 Showcase 版块展示用户用例

**建议分类**：
- 💬 General（综合讨论）
- ❓ Q&A（问答）
- 💡 Ideas（功能建议）
- 🎉 Showcase（用户展示）
- 📢 Announcements（公告）

---

## 5. 启用 Projects（项目看板）

Settings → General → Features → 勾选 **Projects**

用于管理开发路线图和 Sprint 任务，展示项目活跃度。

---

## 6. 保护分支规则

Settings → Branches → Add branch protection rule

**建议规则**：
- Branch name pattern: `main`
- Require pull request reviews before merging: ✅
- Require status checks to pass before merging: ✅（CI 必须通过）
- Require conversation resolution before merging: ✅

---

## 7. 验证清单

配置完成后，用无痕浏览器打开仓库首页，检查：

- [ ] 标题下方是否显示 Description
- [ ] 是否看到 Social Preview 图
- [ ] 侧边栏是否显示 Topics
- [ ] 是否有 "About"  section
- [ ] "Releases" 是否有 v0.1.0

---

## 8. 首次发布 Release

1. 点击仓库右侧 **Releases** → **Create a new release**
2. Choose a tag: `v0.1.0`
3. Release title: `🎉 v0.1.0 - 首次开源发布`
4. Description:

```markdown
## 🎉 首次开源发布

WeChat AI Bot 正式开源！

### ✨ 核心功能
- 多模型 AI 对话（9 Provider，32+ 模型）
- Battle Mode 双模型 PK
- RAG 知识库（PDF/Word/CSV）
- Chain-of-Thought 可视化
- Docker 一键部署

### 🚀 快速开始

\`\`\`bash
git clone https://github.com/xiehuaian77-sketch/wechat-ai-bot.git
cd wechat-ai-bot
docker compose up -d
\`\`\`

### 📖 文档
- [中文 README](README.md)
- [English README](README.en.md)
- [贡献指南](CONTRIBUTING.md)

### ⭐ 如果喜欢这个项目，请给个 Star！
```

5. 勾选 **Set as the latest release**
6. 点击 **Publish release**
