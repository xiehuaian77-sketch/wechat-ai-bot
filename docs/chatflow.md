# Chatflow 可视化编排

Chatflow 是 WeChat AI Bot 的可视化人设编排系统，支持通过简单的配置创建复杂的 AI 对话逻辑。

---

## 🎯 什么是 Chatflow？

Chatflow 是一种**低代码的 AI 对话编排方式**，通过配置节点和边来定义对话流程：

```
[开始] → [判断意图] → [调用工具] → [生成回复] → [结束]
```

相比传统的 Prompt 方式，Chatflow 更适合：
- 多步骤的复杂对话
- 条件分支逻辑
- 工具调用与结果处理
- 人设状态管理

---

## 📋 配置示例

### 基础 Chatflow

```yaml
# config/chatflow/assistant.yaml
name: 智能助手
version: 1.0.0

nodes:
  - id: start
    type: start
    next: classify_intent

  - id: classify_intent
    type: llm
    prompt: |
      判断用户意图：
      - 天气 → weather
      - 搜索 → search
      - 其他 → chat

      用户输入：{{input}}

      意图：
    next:
      weather: handle_weather
      search: handle_search
      chat: generate_reply

  - id: handle_weather
    type: tool
    tool: weather
    params:
      city: "{{extract_city(input)}}"
    next: format_reply

  - id: handle_search
    type: tool
    tool: search
    params:
      query: "{{input}}"
    next: format_reply

  - id: generate_reply
    type: llm
    prompt: |
      你是友好的 AI 助手。
      用户输入：{{input}}

      回复：
    next: format_reply

  - id: format_reply
    type: transform
    template: "{{output}}"
    next: end

  - id: end
    type: end
```

### 带记忆的 Chatflow

```yaml
name: 带记忆的助手
nodes:
  - id: start
    type: start
    next: load_memory

  - id: load_memory
    type: memory
    action: load
    user_id: "{{user_id}}"
    next: generate_reply

  - id: generate_reply
    type: llm
    prompt: |
      历史对话：
      {{memory}}

      用户输入：{{input}}

      回复：
    next: save_memory

  - id: save_memory
    type: memory
    action: save
    user_id: "{{user_id}}"
    content: "{{output}}"
    next: end

  - id: end
    type: end
```

---

## 🔧 节点类型

### 1. Start / End

流程的开始和结束节点。

```yaml
type: start
next: next_node_id
```

### 2. LLM

调用 AI 模型生成回复。

```yaml
type: llm
prompt: |
  你是 AI 助手。
  用户输入：{{input}}

  回复：
model: gpt-4o-mini
temperature: 0.7
max_tokens: 2000
next: next_node_id
```

### 3. Tool

调用工具（天气、搜索等）。

```yaml
type: tool
tool: weather
params:
  city: "北京"
  days: 3
next: next_node_id
```

### 4. Memory

记忆读写。

```yaml
type: memory
action: load  # 或 save
user_id: "{{user_id}}"
content: "{{output}}"  # save 时需要
next: next_node_id
```

### 5. Transform

数据转换。

```yaml
type: transform
template: "结果：{{output}}"
next: next_node_id
```

### 6. Condition

条件分支。

```yaml
type: condition
conditions:
  - if: "{{intent}} == 'weather'"
    next: handle_weather
  - if: "{{intent}} == 'search'"
    next: handle_search
  - default: generate_reply
```

---

## 🎨 可视化编辑器

### 启动编辑器

```bash
# 开发模式
uvicorn app.main:app --reload

# 访问
http://localhost:8000/chatflow
```

### 编辑器功能

- **拖拽节点**：从左侧面板拖拽节点到画布
- **连接节点**：点击节点的输出端口，拖拽到另一个节点的输入端口
- **编辑配置**：点击节点，在右侧面板编辑配置
- **测试运行**：点击"测试"按钮，输入测试用例
- **导出配置**：导出为 YAML 或 JSON

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存 |
| `Ctrl + Z` | 撤销 |
| `Ctrl + Y` | 重做 |
| `Delete` | 删除选中节点 |
| `Space + 拖拽` | 平移画布 |
| `Ctrl + 滚轮` | 缩放 |

---

## 📝 内置变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `{{input}}` | 用户输入 | "今天北京天气" |
| `{{output}}` | 上一步输出 | "北京今天晴" |
| `{{user_id}}` | 用户 ID | "wxid_123" |
| `{{bot_id}}` | 机器人 ID | "bot_001" |
| `{{timestamp}}` | 当前时间戳 | "2026-08-12T10:00:00Z" |
| `{{intent}}` | 意图分类结果 | "weather" |
| `{{memory}}` | 历史记忆 | "用户之前问过天气" |

---

## 🚀 快速开始

### 1. 创建 Chatflow

```bash
# 创建配置文件
mkdir -p config/chatflow
cp config/chatflow/example.yaml config/chatflow/my-assistant.yaml
```

### 2. 编辑配置

使用可视化编辑器或手动编辑 YAML。

### 3. 测试运行

```bash
# 在管理后台测试
curl -X POST http://localhost:8000/api/v1/chatflow/test \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "my-assistant",
    "input": "今天北京天气"
  }'
```

### 4. 部署上线

```bash
# 上传配置
curl -X POST http://localhost:8000/api/v1/admin/chatflow/deploy \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@config/chatflow/my-assistant.yaml"
```

---

## 📚 最佳实践

### 1. 模块化设计

将复杂流程拆分为多个小 Chatflow：

```
main-flow.yaml → weather-flow.yaml
               → search-flow.yaml
               → chat-flow.yaml
```

### 2. 错误处理

```yaml
nodes:
  - id: call_llm
    type: llm
    prompt: "{{input}}"
    on_error:
      next: handle_error
      retry: 3

  - id: handle_error
    type: transform
    template: "抱歉，我遇到了一些问题，请稍后再试。"
    next: end
```

### 3. 日志追踪

```yaml
nodes:
  - id: log_input
    type: log
    level: INFO
    message: "User input: {{input}}"
    next: next_node
```

---

## 🔗 相关文档

- [管理后台 API](../admin-api.md)
- [配置说明](../configuration.md)
- [开发指南](../development.md)

---

最后更新：2026-08-12
