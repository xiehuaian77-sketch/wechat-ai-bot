# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml .
RUN uv sync --frozen --no-dev

# ---- Runtime Stage ----
FROM python:3.12-slim

WORKDIR /app

# 运行时依赖（仅 curl 用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY --chown=appuser:appuser . .

# 非 root 用户运行
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV APP_ENV=production
ENV DEBUG=false

# 创建数据目录
RUN mkdir -p /app/data /app/logs && chown -R appuser:appuser /app/data /app/logs

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]