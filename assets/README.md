# 截图与素材指南

本目录存放项目 README 和文档所需的截图、GIF、图片素材。

---

## 📸 需要的素材清单

### 1. 主界面截图（必填）
- **文件名**：`main-interface.png`
- **尺寸**：`1280 × 720 px`（16:9）
- **内容**：FastAPI 自动文档页（`/docs`）或管理后台首页
- **建议**：展示聊天界面 + 侧边栏模型选择

### 2. 微信对话演示 GIF（必填）
- **文件名**：`wechat-demo.gif`
- **尺寸**：`600 × 600 px`（正方形）
- **时长**：`15-30 秒`
- **内容**：
  1. 打开微信，找到 Bot
  2. 发送"今天北京天气怎么样？"
  3. 等待自动回复
  4. 发送"@battle GPT-4 vs Claude：量子计算会取代经典计算机吗？"
  5. 展示 Battle Mode 结果
  6. 上传 PDF 文件并提问

**录制工具**：
- Windows：`Win + G`（Xbox Game Bar）
- macOS：`Shift + Command + 5`
- 工具：[ScreenToGif](https://www.screentogif.com/)（推荐，可编辑帧）

### 3. 架构图（可选）
- **文件名**：`architecture.png`
- **尺寸**：`1200 × 800 px`
- **内容**：系统架构图（已有 Mermaid 版本，可导出为 PNG）

### 4. 功能特性图（可选）
- **文件名**：`features.png`
- **尺寸**：`1280 × 640 px`
- **内容**：4-6 个核心功能点，带图标

### 5. 移动端截图（可选）
- **文件名**：`mobile-view.png`
- **尺寸**：`390 × 844 px`（iPhone 14 尺寸）
- **内容**：手机上查看管理后台

---

## 🎨 设计规范

| 项目 | 规范 |
|------|------|
| 配色 | 品牌色 `#4ecdc4`（青色）+ `#ff6b6b`（红色） |
| 字体 | 系统默认无衬线字体 |
| 背景 | 深色模式 `#1a1a2e` 或浅色模式 `#ffffff` |
| 圆角 | 统一 `8px` |
| 阴影 | 轻微阴影 `0 4px 6px rgba(0,0,0,0.1)` |

---

## 📝 提交到 README

完成素材后，在 `README.md` 中替换占位符：

```markdown
<!-- 替换前 -->
<img src="https://via.placeholder.com/600x340/1a1a2e/ffffff?text=Demo+GIF+Coming+Soon">

<!-- 替换后 -->
<img src="assets/wechat-demo.gif" alt="WeChat AI Bot Demo" width="600">
```

---

## 🚀 压缩建议

- PNG 使用 [TinyPNG](https://tinypng.com/) 压缩
- GIF 使用 [EZGIF](https://ezgif.com/optimize) 压缩
- 单文件控制在 `2MB` 以内
