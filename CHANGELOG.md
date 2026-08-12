# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 项目初始化，基于 FastAPI + LangGraph + ChromaDB 的 AI 微信机器人骨架
- ComWeChatRobot Hook 接入，支持私聊/群聊/图片/文件消息
- LangGraph 四节点 Agent 引擎（Planner → Executor → Reflector → Responder）
- Function Calling 工具集：天气、日期时间、汇率、代码执行、网页搜索
- RAG 知识库：ChromaDB 向量检索，支持 PDF/Word/CSV 上传
- 管理后台 API：用户管理、对话历史、工单系统、人工审批（HITL）
- 可观测性指标：响应延迟、Token 消耗、工具成功率
- Docker Compose 一键部署（含 ChromaDB + Nginx）

### Security
- JWT 认证与 RBAC 权限控制
- 限流中间件（全局限流 + IP 限流）
- 管理员白名单/群聊黑名单

## [0.1.0] - 2026-08-12

### Added
- 首次开源发布
- 完整 README + 架构图
- 单元测试与集成测试
- GitHub Actions CI（lint / test / security scan）
- 英文 README / CONTRIBUTING / CODE_OF_CONDUCT
