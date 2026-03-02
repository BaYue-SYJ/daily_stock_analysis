# AI News SaaS (FastAPI)

一个面向 AI 行业资讯自动化运营的多租户 SaaS 样板：
- 自动抓取 RSS
- 调用 GPT 总结
- 发布到微信公众号
- 提供小程序读取 API

## 项目结构

```text
ai_news_saas/
  app/
    api/            # FastAPI 路由（auth/users/content/publish/mini）
    core/           # 配置与安全（JWT、密码）
    db/             # SQLAlchemy 会话与初始化
    models/         # ORM 模型
    services/       # 抓取、总结、微信发布服务
    tasks/          # Celery worker/beat 任务
  docs/             # API 设计与数据库 SQL
  docker-compose.yml
  Dockerfile
  .env.example
```

## 本地运行（Docker）

### 1) 准备环境变量

```bash
cp .env.example .env
```

> 必填：`OPENAI_API_KEY`

### 2) 启动服务

```bash
docker compose up --build -d
```

包含服务：
- `web`：FastAPI
- `worker`：Celery Worker
- `beat`：Celery Beat（每日 09:00 和 18:00 调度）
- `redis`
- `mysql`

### 3) 打开接口文档

- Swagger: http://localhost:8000/docs

## 快速验证

```bash
docker compose ps
docker compose logs web --tail 100
docker compose logs worker --tail 100
docker compose logs beat --tail 100
```

## 典型调用流程

1. `POST /api/v1/auth/register` 注册租户管理员
2. `POST /api/v1/auth/login` 登录获取 JWT
3. `POST /api/v1/content/rss` 添加 RSS 源
4. `POST /api/v1/content/sync` 触发抓取+总结任务
5. `GET /api/v1/mini/articles` 小程序分页拉取文章

## 发布到 GitHub 的建议

1. 确保 `.env` 未提交（已在 `.gitignore` 处理）。
2. 在仓库设置 `OPENAI_API_KEY` 等 Actions Secret（如需 CI/CD）。
3. 打 tag：`v0.1.0` 并发布 Release。
4. 在 Release 描述中附上：
   - 启动命令
   - 环境变量清单
   - 首次调用流程

## 文档

- API 设计：`docs/api_design.md`
- 数据库结构：`docs/database_schema.sql`、`docs/database_schema_step2.sql`
